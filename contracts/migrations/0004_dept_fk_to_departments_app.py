import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contracts', '0003_add_contract_file'),
        ('departments', '0002_rename_tables'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='contract',
                    name='department',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='contracts',
                        to='departments.department',
                        verbose_name='Phòng ban',
                    ),
                ),
            ],
        ),
    ]
