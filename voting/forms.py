from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Election, Position, Candidate, VoterProfile, Vote


class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ['name', 'description', 'starts_at', 'ends_at', 'published']
        widgets = {
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()
            if field.required:
                field.widget.attrs['required'] = 'required'


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['title', 'description', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['student', 'name', 'bio', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'photo':
                field.widget.attrs.setdefault('class', 'form-control')


class VoterProfileForm(forms.ModelForm):
    """Used by staff to create a voter together with a login account."""

    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = VoterProfile
        fields = ['student_id', 'department', 'gender', 'year_of_study', 'session', 'is_verified']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()

    def clean_username(self):
        from django.contrib.auth.models import User
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class BallotForm(forms.Form):
    """Dynamic form: one radio-select per position in the election."""

    def __init__(self, *args, election=None, voter=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.positions = list(
            election.positions.filter(candidates__isnull=False).distinct()
            if election else []
        )
        for position in self.positions:
            self.fields[f'position_{position.pk}'] = forms.ModelChoiceField(
                queryset=position.candidates.all(),
                widget=forms.RadioSelect,
                label=position.title,
                required=False,  # abstaining is allowed
            )
