from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from reports.views import dashboard

@login_required
def home(request):
    return dashboard(request)
