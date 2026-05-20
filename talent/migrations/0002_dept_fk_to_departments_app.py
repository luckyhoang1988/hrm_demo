import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('talent', '0001_initial'),
        ('departments', '0002_rename_tables'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='jobposition',
                    name='department',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='job_positions',
                        to='departments.department',
                    ),
                ),
                migrations.AlterField(
                    model_name='trainingcourse',
                    name='target_departments',
                    field=models.ManyToManyField(
                        blank=True,
                        related_name='training_courses',
                        to='departments.department',
                    ),
                ),
            ],
        ),
    ]
