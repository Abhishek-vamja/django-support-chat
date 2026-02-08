from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Visitor',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('mobile', models.CharField(max_length=20, blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SupportAgent',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('is_active', models.BooleanField(default=True)),
                ('is_online', models.BooleanField(default=False)),
                ('max_concurrent_chats', models.PositiveIntegerField(default=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('status', models.CharField(default='waiting', max_length=20)),
                ('assigned_at', models.DateTimeField(blank=True, null=True)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('feedback', models.TextField(blank=True)),
                ('assigned_agent', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='conversations', to='support_chat.supportagent')),
                ('visitor', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='conversations', to='support_chat.visitor')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('sender_type', models.CharField(max_length=10)),
                ('sender_id', models.UUIDField(blank=True, null=True)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='messages', to='support_chat.conversation')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='ConversationRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_rating', models.PositiveSmallIntegerField()),
                ('system_rating', models.PositiveSmallIntegerField()),
                ('comment', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='rating_obj', to='support_chat.conversation')),
            ],
        ),
    ]
