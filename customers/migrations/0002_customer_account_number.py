from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='account_number',
            field=models.CharField(blank=True, default='', help_text='Customer account number shown on quotations and invoices', max_length=50),
        ),
    ]