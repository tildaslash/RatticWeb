from django.db import models
from django.contrib.auth.models import User, Group
from django import forms

class NewUserForm(forms.ModelForm):
    # We want two password input boxes
    newpass = forms.CharField(widget=forms.PasswordInput, max_length=32, min_length=8)
    confirmpass = forms.CharField(widget=forms.PasswordInput, max_length=32, min_length=8)

    # Define our model
    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff', 'groups')

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        # Use checkboxes for groups
        self.fields["groups"].widget = forms.CheckboxSelectMultiple()
        self.fields["groups"].queryset = Group.objects.all()

    def clean(self):
        # Check the passwords given match
        cleaned_data = super(NewUserForm, self).clean()
        newpass = cleaned_data.get("newpass")
        confirmpass = cleaned_data.get("confirmpass")

        if newpass != confirmpass:
            msg = u'Passwords do not match'
            self._errors['confirmpass'] = self.error_class([msg])
            del cleaned_data['newpass']
            del cleaned_data['confirmpass']

        return cleaned_data



