from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0004_review_rating_and_tagbind_constraints'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='copy',
            name='holder',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='held_copies',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Текущий держатель',
            ),
        ),
    ]
