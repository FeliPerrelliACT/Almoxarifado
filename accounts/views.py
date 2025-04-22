from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.contrib.auth.views import LoginView
from django.contrib.auth import get_user_model
from accounts.forms import accountsignupForm
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse_lazy
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

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        messages.error(self.request, 'Usuário ou senha incorretos.')
        return super().form_invalid(form)

def remover_imagem(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Verifica se o usuário tem uma imagem associada
    if user.imagem:
        user.imagem.delete()  # Remove a imagem do sistema de arquivos
        user.imagem = None  # Remove a referência no banco de dados
        user.save()
        messages.success(request, "Imagem de perfil removida com sucesso!")
    else:
        messages.error(request, "Nenhuma imagem para remover.")
    
    return redirect('editar_perfil')  # Redireciona para a página de edição de perfil
