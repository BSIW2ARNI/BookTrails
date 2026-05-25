from __future__ import annotations

import math
import re
from collections import defaultdict

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Prefetch, Q, Value
from django.db.models.functions import Coalesce

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Author, Book, Recommendation, Review


TOKEN_RE = re.compile(r"[A-Za-zА-Яа-я0-9]+", re.UNICODE)


def _normalize_text(value: str) -> str:
    tokens = TOKEN_RE.findall((value or "").lower())
    return " ".join(token for token in tokens if len(token) > 1)


def _prefetched_authors():
    return Prefetch(
        "authors",
        queryset=Author.objects.order_by("book_authors__sort_order", "name"),
        to_attr="prefetched_authors",
    )


def build_book_document(book: Book) -> str:
    authors = getattr(book, "prefetched_authors", None) or []
    author_names = " ".join(author.name for author in authors)
    genre_name = book.genre.name if book.genre_id else ""
    language_name = book.language.name if book.language_id else ""
    reviews_blob = " ".join(getattr(book, "prefetched_review_texts", []))

    parts = [
        book.title,
        author_names,
        genre_name,
        language_name,
        book.description or "",
        reviews_blob,
    ]
    return _normalize_text(" ".join(part for part in parts if part))


def get_recommendation_candidates() -> list[Book]:
    books = (
        Book.objects.select_related("genre", "language")
        .prefetch_related(_prefetched_authors(), "reviews")
        .annotate(
            rating=Coalesce(Avg("reviews__rating"), Value(0.0)),
            reviews_count=Count("reviews", distinct=True),
        )
        .order_by("id")
    )

    prepared_books: list[Book] = []
    for book in books:
        review_texts = [review.text for review in book.reviews.all() if review.text]
        setattr(book, "prefetched_review_texts", review_texts)
        prepared_books.append(book)
    return prepared_books


def _build_vectorizer(books: list[Book]):
    documents = [build_book_document(book) for book in books]
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
    )
    matrix = vectorizer.fit_transform(documents)
    return matrix


def _get_positive_user_books(user: User) -> list[tuple[int, float]]:
    reviewed_books = (
        Review.objects.filter(author=user)
        .select_related("book")
        .order_by("-rating", "-created_at")
    )

    weighted_books: dict[int, float] = {}
    for review in reviewed_books:
        if review.rating >= 4:
            weighted_books[review.book_id] = max(weighted_books.get(review.book_id, 0.0), float(review.rating))

    return list(weighted_books.items())


def _fallback_popular_books(books: list[Book], limit: int) -> list[dict]:
    ranked = sorted(
        books,
        key=lambda book: (
            float(getattr(book, "rating", 0.0) or 0.0),
            int(getattr(book, "reviews_count", 0) or 0),
            book.id,
        ),
        reverse=True,
    )
    results = []
    for book in ranked[:limit]:
        results.append(
            {
                "book": book,
                "score": float(getattr(book, "rating", 0.0) or 0.0),
                "explanation": "Рекомендация выбрана по популярности и рейтингу книги.",
            }
        )
    return results


def generate_recommendations_for_user(user: User, *, limit: int = 10) -> list[dict]:
    books = get_recommendation_candidates()
    if not books:
        return []

    positive_books = _get_positive_user_books(user)
    if not positive_books:
        return _fallback_popular_books(books, limit)

    book_index = {book.id: index for index, book in enumerate(books)}
    matrix = _build_vectorizer(books)

    user_profile = None
    for book_id, weight in positive_books:
        index = book_index.get(book_id)
        if index is None:
            continue
        weighted_vector = matrix[index] * weight
        user_profile = weighted_vector if user_profile is None else user_profile + weighted_vector

    if user_profile is None:
        return _fallback_popular_books(books, limit)

    similarities = cosine_similarity(user_profile, matrix).flatten()
    seen_book_ids = {book_id for book_id, _weight in positive_books}

    results: list[dict] = []
    for book, score in sorted(
        zip(books, similarities, strict=True),
        key=lambda item: item[1],
        reverse=True,
    ):
        if book.id in seen_book_ids:
            continue
        if math.isclose(float(score), 0.0):
            continue

        results.append(
            {
                "book": book,
                "score": float(score),
                "explanation": "Книга похожа по описанию, жанру и смыслу пользовательских отзывов.",
            }
        )
        if len(results) >= limit:
            break

    if results:
        return results
    return _fallback_popular_books([book for book in books if book.id not in seen_book_ids], limit)


def persist_recommendations_for_user(user: User, *, limit: int = 10) -> list[Recommendation]:
    recommendations = generate_recommendations_for_user(user, limit=limit)
    Recommendation.objects.filter(user=user).delete()

    created: list[Recommendation] = []
    for item in recommendations:
        created.append(
            Recommendation.objects.create(
                user=user,
                book=item["book"],
                score=round(float(item["score"]), 4),
                explanation=item["explanation"],
            )
        )
    return created


def persist_recommendations_for_all_users(*, limit: int = 10) -> dict[str, int]:
    stats: dict[str, int] = defaultdict(int)
    for user in User.objects.filter(is_active=True).order_by("id"):
        created = persist_recommendations_for_user(user, limit=limit)
        stats[user.username] = len(created)
    return dict(stats)
