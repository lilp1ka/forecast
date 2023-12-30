from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MaxValueValidator
from django.utils import timezone

class Transaction(models.Model):
    """CATEGORY_CHOICES = (
                        ('food', 'Food and Drinks'),
                        ('housing', 'Housing'),
                        ('transportation', 'Transportation'),
                        ('health', 'Health'),
                        ('education', 'Education'),
                        ('entertainment', 'Entertainment'),
                        ('personal_expenses', 'Personal Expenses'),
                        ('financial_obligations', 'Financial Obligations'),
                        ('savings', 'Savings'),
                        ('others', 'Others'),)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    category = models.CharField(max_length=25, default='others')
    amount = models.IntegerField(validators=[MaxValueValidator(limit_value=9999999999)], default=0)
    time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    description = models.CharField(max_length=50, default='')
    currency=models.CharField(max_length = 25, default='ZL')
    title = models.CharField(max_length = 40, default = '')
    

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null = True, blank = True)
    title = models.CharField(max_length=20)
    description = models.CharField(max_length=50,null = True, blank=True)
    complete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True, default=timezone.now)
    
class FriendPhone(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null = True, blank = True)
    fname = models.CharField(max_length=20)
    fsurname = models.CharField(max_length=20)
    fmail = models.EmailField(null=True,blank=True)
    fbirthday = models.DateField(null=True,blank=True,default=timezone.now)
    
class BObject(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null = True, blank = True)
    object_name = models.CharField(max_length=20)
    object_desc = models.CharField(max_length=20)
    first_price = models.FloatField(null=True,blank=True)
    first_date = models.DateTimeField(null=True,blank=True)
    second_price = models.FloatField(null=True,blank=True)
    second_date = models.DateTimeField(null=True,blank=True,default=timezone.now)
