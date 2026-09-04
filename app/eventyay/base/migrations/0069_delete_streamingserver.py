from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0068_invoicevoucher_status_comment_partial_usage'),
    ]

    operations = [
        migrations.DeleteModel(
            name='StreamingServer',
        ),
    ]
