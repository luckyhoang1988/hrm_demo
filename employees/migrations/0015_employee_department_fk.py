from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0014_add_status_date_range'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='department_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='employees',
                to='employees.department',
            ),
        ),
    ]
