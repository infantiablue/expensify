from django.forms import ModelForm
from django import forms
from .models import User, Transaction, Category


class NewTransactionForm(ModelForm):
    class Meta:
        model = Transaction
        fields = ['text', 'amount', 'category']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            user=user).order_by('title')

    text = forms.CharField(label='Description', widget=forms.TextInput(
        attrs={'class': 'form-control'}), required=True, max_length=255)
    amount = forms.FloatField(widget=forms.TextInput(
        attrs={'class': 'form-control'}), required=True)


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['title', 'source']
        widgets = {
            'source': forms.RadioSelect(attrs={'class': 'category-source'}),
        }

    title = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control'}), required=True, max_length=128)


class CustomFileInput(forms.ClearableFileInput):
    template_name = 'tracker/widgets/forms/avatar.html'


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar']

    first_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control mb-2'}))
    last_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control mb-2'}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control mb-2'}), disabled=True)
    avatar = forms.ImageField(widget=CustomFileInput(), required=False)

    # def clean_avatar(self):
    #     print(self.cleaned_data['avatar'])
    #     if self.cleaned_data['avatar']:
    #         return self.cleaned_data['avatar']
    #     else:
    #         return None
