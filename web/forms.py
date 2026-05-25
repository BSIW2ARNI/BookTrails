from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import MoveEventType, Review, UserProfile


class LoginForm(forms.Form):
    login = forms.CharField(
        label='Email или логин',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'reader@booktrail.io'}),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
    )

    error_messages = {
        'invalid_login': 'Неверный логин/email или пароль.',
        'inactive': 'Этот аккаунт отключен.',
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache: User | None = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        credential = (cleaned_data.get('login') or '').strip()
        password = cleaned_data.get('password') or ''
        if not credential or not password:
            return cleaned_data

        self.user_cache = authenticate(self.request, username=credential, password=password)
        if self.user_cache is None:
            user = User.objects.filter(email__iexact=credential).first()
            if user:
                self.user_cache = authenticate(self.request, username=user.username, password=password)

        if self.user_cache is None:
            raise ValidationError(self.error_messages['invalid_login'])
        if not self.user_cache.is_active:
            raise ValidationError(self.error_messages['inactive'])
        return cleaned_data

    def get_user(self) -> User | None:
        return self.user_cache


class RegisterForm(forms.Form):
    full_name = forms.CharField(
        label='Отображаемое имя',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Алиса Морозова'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'reader@booktrail.io'}),
    )
    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Минимум 8 символов'}),
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите пароль'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Пароли не совпадают.')
        return cleaned_data

    def save(self) -> User:
        if not self.is_valid():
            raise ValueError('Cannot save invalid form.')

        full_name = self.cleaned_data['full_name'].strip()
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']

        user = User(
            username=email,
            email=email,
            is_active=True,
        )

        name_parts = full_name.split(maxsplit=1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''

        password_validation.validate_password(password, user)
        user.set_password(password)
        user.save()
        return user


class ProfileForm(forms.Form):
    full_name = forms.CharField(
        label='Имя и фамилия',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Алиса Морозова'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'reader@booktrail.io'}),
    )
    avatar = forms.CharField(
        label='Аватар',
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'AM'}),
    )
    status = forms.CharField(
        label='Статус',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Исследователь маршрутов'}),
    )
    show_profile = forms.BooleanField(label='Показывать профиль', required=False)
    share_reviews = forms.BooleanField(label='Делиться отзывами', required=False)
    nfc_visibility = forms.BooleanField(label='Показывать NFC-статус', required=False)

    def __init__(self, *, user: User, profile: UserProfile, **kwargs):
        self.user = user
        self.profile = profile
        initial = kwargs.setdefault('initial', {})
        initial.setdefault('full_name', user.get_full_name().strip())
        initial.setdefault('email', user.email)
        initial.setdefault('avatar', profile.avatar)
        initial.setdefault('status', profile.status)
        initial.setdefault('show_profile', profile.show_profile)
        initial.setdefault('share_reviews', profile.share_reviews)
        initial.setdefault('nfc_visibility', profile.nfc_visibility)
        super().__init__(**kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        exists = User.objects.exclude(pk=self.user.pk).filter(Q(email__iexact=email) | Q(username__iexact=email)).exists()
        if exists:
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_avatar(self):
        return (self.cleaned_data.get('avatar') or '').strip().upper()[:8]

    def save(self) -> UserProfile:
        full_name = self.cleaned_data['full_name'].strip()
        email = self.cleaned_data['email']
        avatar = self.cleaned_data['avatar']
        status = self.cleaned_data['status'].strip()

        name_parts = full_name.split(maxsplit=1)
        self.user.first_name = name_parts[0] if name_parts else ''
        self.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        self.user.email = email
        self.user.username = email
        self.user.save(update_fields=['first_name', 'last_name', 'email', 'username'])

        self.profile.avatar = avatar
        self.profile.status = status
        self.profile.show_profile = self.cleaned_data['show_profile']
        self.profile.share_reviews = self.cleaned_data['share_reviews']
        self.profile.nfc_visibility = self.cleaned_data['nfc_visibility']
        self.profile.save(update_fields=['avatar', 'status', 'show_profile', 'share_reviews', 'nfc_visibility', 'updated_at'])
        return self.profile


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'text': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Что вам запомнилось в маршруте этой книги?'}),
        }
        labels = {
            'rating': 'Оценка',
            'text': 'Отзыв',
        }

    def clean_rating(self):
        rating = self.cleaned_data['rating']
        if rating < 1 or rating > 5:
            raise ValidationError('Оценка должна быть от 1 до 5.')
        return rating


class MoveForm(forms.Form):
    event_type = forms.ModelChoiceField(
        label='Тип события',
        queryset=MoveEventType.objects.none(),
        empty_label='Выберите тип',
    )
    place_text = forms.CharField(
        label='Место',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Книжный шкаф у метро'}),
    )
    text = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Книга передана следующему читателю.'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event_type'].queryset = MoveEventType.objects.exclude(code='scan').order_by('title')


class NfcBindForm(forms.Form):
    tag_uid = forms.CharField(
        label='UID NFC-метки',
        max_length=64,
        widget=forms.TextInput(attrs={'placeholder': '04A1B2C3D4'}),
    )

    def clean_tag_uid(self):
        value = (self.cleaned_data['tag_uid'] or '').strip().upper()
        if not value:
            raise ValidationError('Введите UID метки.')
        return value


class ScanForm(forms.Form):
    copy_code = forms.CharField(
        label='Код экземпляра',
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'BT-001'}),
    )
    tag_uid = forms.CharField(
        label='UID метки',
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '04A1B2C3D4'}),
    )
    place_text = forms.CharField(
        label='Место',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Полка сообщества на Покровке'}),
    )
    text = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Метка считана, книга готова к передаче.'}),
    )

    def clean_copy_code(self):
        return (self.cleaned_data.get('copy_code') or '').strip().upper()

    def clean_tag_uid(self):
        return (self.cleaned_data.get('tag_uid') or '').strip().upper()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('copy_code') and not cleaned_data.get('tag_uid'):
            raise ValidationError('Укажите код экземпляра или UID метки.')
        return cleaned_data
