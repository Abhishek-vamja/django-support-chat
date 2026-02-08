from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('support_chat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('otp', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('attempts', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AgentSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_token', models.CharField(db_index=True, max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('agent', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='session', to='support_chat.supportagent')),
            ],
        ),
    ]
