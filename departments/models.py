from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class EmployeeGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)
    departments = models.ManyToManyField(Department, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
