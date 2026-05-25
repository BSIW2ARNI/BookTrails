from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_copystatus_moveeventtype_movesource_nfctagstatus_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='review',
            constraint=models.CheckConstraint(
                condition=models.Q(('rating__gte', 1), ('rating__lte', 5)),
                name='review_rating_between_1_and_5',
            ),
        ),
        migrations.AddConstraint(
            model_name='tagbind',
            constraint=models.CheckConstraint(
                condition=models.Q(('ended_at__isnull', True), ('ended_at__gte', models.F('started_at')), _connector='OR'),
                name='tag_bind_end_after_start',
            ),
        ),
    ]
