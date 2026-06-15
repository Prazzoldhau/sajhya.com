from django import forms
from .models import AddPatient

class PatientForm(forms.ModelForm):
    class Meta:
        model = AddPatient
        fields = ['patient_name', 'patient_contact', 'completed_session', 'patient_diagnosis']
        # Note: patient_code and created_by are excluded (auto-generated / set in view)
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'patient_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'completed_session': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'enter 0 if none'}),  # ✅ fixed widget
            'patient_diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Diagnosis details'}),
        }

    # Custom validation examples
    def clean_patient_name(self):
        name = self.cleaned_data.get('patient_name')
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters long.')
        return name

    def clean_patient_contact(self):
        contact = self.cleaned_data.get('patient_contact')
        if not contact.isdigit():
            raise forms.ValidationError('Contact number must contain only digits.')
        if len(contact) < 10:
            raise forms.ValidationError('Enter a valid phone number (at least 10 digits).')
        return contact

    def clean_patient_diagnosis(self):
        diagnosis = self.cleaned_data.get('patient_diagnosis')
        if len(diagnosis) < 5:
            raise forms.ValidationError('Diagnosis must be at least 5 characters.')
        return diagnosis
    
            # ✅ Optional: add validation for completed_session (past session number)
    def clean_completed_session(self):
        sessions = self.cleaned_data.get('completed_session')
        if sessions is None:
            return sessions
        if sessions < 0:
            raise forms.ValidationError('Completed sessions cannot be negative.')
        # You can also add an upper limit if needed
        return sessions
    