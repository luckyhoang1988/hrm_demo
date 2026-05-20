from django.db import migrations, models
import django.db.models.deletion


def populate_department_fk(apps, schema_editor):
    """Copy dữ liệu từ department CharField sang department_fk ForeignKey."""
    Employee = apps.get_model('employees', 'Employee')
    Department = apps.get_model('employees', 'Department')
    dept_cache = {}
    for emp in Employee.objects.all():
        name = emp.department  # CharField cũ
        if name not in dept_cache:
            dept_obj, _ = Department.objects.get_or_create(name=name)
            dept_cache[name] = dept_obj
        emp.department_fk = dept_cache[name]
        emp.save()


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0015_employee_department_fk'),
    ]

    operations = [
        # Bước 1: Copy dữ liệu từ CharField sang FK
        migrations.RunPython(populate_department_fk, migrations.RunPython.noop),

        # Bước 2: Bắt buộc FK (không được NULL nữa)
        migrations.AlterField(
            model_name='employee',
            name='department_fk',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='employees',
                to='employees.department',
            ),
        ),

        # Bước 3: Xóa cột CharField cũ
        migrations.RemoveField(
            model_name='employee',
            name='department',
        ),

        # Bước 4: Đổi tên department_fk → department
        migrations.RenameField(
            model_name='employee',
            old_name='department_fk',
            new_name='department',
        ),
    ]
