from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Transaction, Task

class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = User
        fields = ['id', 'username', 'password', 'email']
        
        
class TransactionSerializer(serializers.ModelSerializer):
    time = serializers.DateTimeField(allow_null=True, required=False)
    class Meta(object):
        model = Transaction
        fields = ['user', 'category','time', 'amount','description', 'currency']
        
        
class TaskSerializer(serializers.ModelSerializer):
    timeleft = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = '__all__'
    
    def get_timeleft(self, obj):
        if obj.deadline and obj.created: 
            time_diff = obj.deadline - obj.created
            return time_diff.total_seconds() if time_diff.total_seconds() > 0 else 0
        return 0