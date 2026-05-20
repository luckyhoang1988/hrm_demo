import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0023_alter_activitylog_target_type'),
        ('departments', '0002_rename_tables'),
        ('contracts', '0004_dept_fk_to_departments_app'),
        ('talent', '0002_dept_fk_to_departments_app'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='employee',
                    name='department',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='employees',
                        to='departments.department',
                    ),
                ),
                migrations.AlterField(
                    model_name='usergrouppermission',
                    name='group',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='user_perms',
                        to='departments.employeegroup',
                    ),
                ),
                migrations.AlterField(
                    model_name='staffgroupdeptperm',
                    name='emp_group',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='staff_perms',
                        to='departments.employeegroup',
                    ),
                ),
                migrations.DeleteModel(name='Department'),
                migrations.DeleteModel(name='EmployeeGroup'),
            ],
        ),
    ]
