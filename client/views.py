# Create your views here.
def home():
    pass

class LoginForm(forms.Form):
    username = fields.CharField(max_length=30, min_length=3)
    password = fields.CharField(max_length=30, widget=forms.PasswordInput)


def login(request):
    redirect_to = request.REQUEST.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].lower()
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                messages.add_message(request, messages.SUCCESS, u"Добро пожаловать, " + username)
                return HttpResponseRedirect(redirect_to)
            else:
                messages.add_message(request, messages.ERROR, u"Ошибка: данной пары логин-пароль не существует.")
    else:
        form=LoginForm()
    return render_to_response(template_name='guide/login.html',
                              dictionary={'form': form, 'next': redirect_to},
                              context_instance=RequestContext(request)
    )
