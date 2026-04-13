# Generated migration: Change fcm_token from CharField to TextField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dispositivos', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='fcm_token',
            field=models.TextField(blank=True),
        ),
    ]
