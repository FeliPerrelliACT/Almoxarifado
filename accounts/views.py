from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from accounts.forms import accountsignupForm
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.shortcuts import render
from django.contrib import messages

User = get_user_model()

class AccountCreateView(LoginRequiredMixin, CreateView):
    model = User
    template_name = 'registration/signup_form.html'
    form_class = accountsignupForm
    success_url = reverse_lazy('index')
    success_message = 'Usuário registrado com sucesso!!!'

    def form_valid(self, form) -> HttpResponse:
        form.instance.password = make_password(form.instance.password)
        form.save()
        messages.success(self.request, self.success_message)

        return super(AccountCreateView, self).form_valid(form)
 
class AccountUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'accounts/user_form.html'
    fields = ('email', 'imagem')
    success_url = reverse_lazy('index')
    success_message = 'Perfil atualizado com sucesso'

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


