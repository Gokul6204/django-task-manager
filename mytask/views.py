import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Task
from django.contrib.auth.models import User

# ---- Login ----
def loginPage(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('userpassword')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('myTask')
        return render(request, 'login.html', {"message": "Invalid Credentials"})
    return render(request, 'login.html')

# ---- Signup ----
def signupPage(request):
    if request.method == "POST":
        username = request.POST.get('username')
        fname = request.POST.get('firstname', '')
        lname = request.POST.get('lastname', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {"error": "Username already exists"})
        new_user = User(username=username, first_name=fname, last_name=lname, email=email)
        new_user.set_password(password)
        new_user.save()
        return redirect('login')
    return render(request, 'signup.html')

# ---- logout ----
@login_required
def logOut(request):
    logout(request)
    return redirect('login')

# ---- Page view ----
@login_required
def myTask(request):
    user = request.user
    tasks = Task.objects.filter(user=user).order_by("-created")
    return render(request, 'myTask.html', {"user": user, "tasks": tasks})

# ---- API endpoints (AJAX) ----
@login_required
@require_POST
def add_task(request):
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        complete = bool(data.get('complete', False))

        if not title:
            return JsonResponse({"success": False, "error": "Title required"}, status=400)

        task = Task.objects.create(user=request.user, title=title, description=description, complete=complete)
        return JsonResponse({
            "success": True,
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "complete": task.complete
        })
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

# ---- Delete Task ----
@login_required
@require_POST
def delete_task(request):
    try:
        data = json.loads(request.body)
        task_id = data.get('id')
        task = Task.objects.get(id=task_id, user=request.user)
        task.delete()
        return JsonResponse({"success": True})
    except Task.DoesNotExist:
        return JsonResponse({"success": False, "error": "Task not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ---- Edit Task ----
@login_required
@require_POST
def edit_task(request):
    try:
        data = json.loads(request.body)
        task_id = data.get('id')
        task = Task.objects.get(id=task_id, user=request.user)

        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.complete = bool(data.get('complete', task.complete))
        task.save()

        return JsonResponse({
            "success": True,
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "complete": task.complete
        })
    except Task.DoesNotExist:
        return JsonResponse({"success": False, "error": "Task not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
