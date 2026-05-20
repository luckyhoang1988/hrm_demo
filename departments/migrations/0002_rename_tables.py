from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('departments', '0001_initial')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$ BEGIN
                            IF EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public' AND table_name = 'employees_department'
                            ) AND NOT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public' AND table_name = 'departments_department'
                            ) THEN
                                ALTER TABLE employees_department RENAME TO departments_department;
                            END IF;
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql="""
                        DO $$ BEGIN
                            IF EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public' AND table_name = 'employees_employeegroup'
                            ) AND NOT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public' AND table_name = 'departments_employeegroup'
                            ) THEN
                                ALTER TABLE employees_employeegroup RENAME TO departments_employeegroup;
                            END IF;
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql="""
                        DO $$ BEGIN
                            IF EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public' AND table_name = 'employees_employeegroup_departments'
                            ) AND NOT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public' AND table_name = 'departments_employeegroup_departments'
                            ) THEN
                                ALTER TABLE employees_employeegroup_departments RENAME TO departments_employeegroup_departments;
                            END IF;
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
    ]
