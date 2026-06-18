from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from personal_account .models import AddPatient
from datetime import date


class Region(models.Model):
    region_name = models.CharField(max_length=100)
    
    
    def __str__(self):
        return self.region_name

class SubRegion(models.Model):
    region_fk = models.ForeignKey(
        "Region", 
        verbose_name=_("Region"), 
        on_delete=models.CASCADE)
    sub_region_name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.sub_region_name
    
class ExerciseType(models.TextChoices):
    ISOMETRIC = 'isometric', 'Isometric'
    STRETCHING = 'stretching', 'Stretching'
    STRENGTHENING = 'strengthening', 'Strengthening'
    ROM = 'rom', 'ROM'
    MOBILITY = 'mobility', 'Mobility'
    POSTURAL = 'postural', 'Postural'
    STABILITY = 'stability', 'Stability'
    FUNCTIONAL = 'functional', 'Functional'
    MCKENZIE = 'mckenzie', 'McKenzie'
    POSTURE_CORRECTION = 'posture_correction', 'Posture Correction'
    NEURODYNAMIC = 'neurodynamic', 'Neurodynamic'
    RELAXATION = 'relaxation', 'Relaxation'
    BALANCE = 'balance', 'Balance'
    COORDINATION = 'coordination', 'Coordination'
    POSTURAL_CONTROL = 'postural_control', 'Postural Control'
    PNF = 'pnf', 'PNF'
    NEGLECT_TRAINING = 'neglect_training', 'Neglect Training'
    GAIT_TRAINING = 'gait_training', 'Gait Training'
    MIRROR_THERAPY = 'mirror_therapy', 'Mirror Therapy'
    MOTOR_RELEARNING = 'motor_relearning', 'Motor Relearning'
    TONE_MANAGEMENT = 'tone_management', 'Tone Management'
    COGNITIVE_MOTOR = 'cognitive_motor', 'Cognitive Motor'
    AQUATIC = 'aquatic', 'Aquatic / Hydrotherapy'
    BFR = 'bfr', 'Blood Flow Restriction (BFR)'
    SUSPENSION = 'suspension', 'Suspension Therapy'
    

class DifficultyLevel(models.IntegerChoices):
    BEGINNER = 1, 'Beginner'
    INTERMEDIATE = 2, 'Intermediate'
    ADVANCED = 3, 'Advanced'
    SUPER = 4, 'Super Level'
    
class ExerciseMain(models.Model):
    sub_region_fk = models.ForeignKey(
        "SubRegion",
        verbose_name=_("SubRegion"),
        on_delete=models.CASCADE
    )

    exercise_name = models.CharField(max_length=100)
    exercise_type = models.CharField(max_length=50, choices=ExerciseType.choices)
    difficulty_level = models.IntegerField(choices=DifficultyLevel.choices)

    default_sets = models.IntegerField()
    default_reps = models.IntegerField()
    hold_time_sec = models.IntegerField()

    exercise_description = models.CharField(max_length=500)
    exercise_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.exercise_name
    
    


class Prescription(models.Model):
    """Model to store exercise prescriptions"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    # Relationship with Patient (from sajhya_app)
    
    patient = models.ForeignKey(
        AddPatient, 
        on_delete=models.CASCADE, 
        related_name='prescriptions'
    )

    # Prescription details
    prescription_date = models.DateTimeField(auto_now_add=True)
    # start_date = models.DateField()
    # end_date = models.DateField()
    # prescription_notes = models.TextField(blank=True, null=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
    
    def __str__(self):
        return f"Prescription #{self.id} - {self.patient}"
    
    
    def get_total_exercises(self):
        """Get total number of exercises in this prescription"""
        return self.exercises.count()
    
    def get_completion_percentage(self):
        """Calculate completion percentage"""
        total = self.exercises.count()
        if total == 0:
            return 0
        completed = self.exercises.filter(is_completed=True).count()
        return round((completed / total) * 100, 1)
    
    def is_active_prescription(self):
        """Check if prescription is currently active"""
        today = date.today()
        return (self.status == 'active' and 
                self.start_date <= today <= self.end_date)
    
    def get_duration_days(self):
        """Get prescription duration in days"""
        return (self.end_date - self.start_date).days

class PrescriptionExercise(models.Model):
    """Model to store individual exercises within a prescription"""
    
    DIFFICULTY_CHOICES = [
        (1, 'Beginner'),
        (2, 'Intermediate'),
        (3, 'Advanced'),
        (4, 'Super Level'),
        
    ]

    # Relationship with Prescription
    prescription = models.ForeignKey(
        Prescription, 
        on_delete=models.CASCADE, 
        related_name='exercises',
        db_column='prescription_id'
    )
    
    # Relationship with Exercise from  (optional - can be null if exercise is deleted)
    exercise = models.ForeignKey(
        ExerciseMain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescription_exercises',
        help_text="Reference to the original exercise from "
    )
    
    # Snapshot of exercise details at time of prescription (stored separately to preserve data)
    exercise_id_in_library = models.IntegerField(
        db_index=True, 
        help_text="ID from the original exercise library in "
    )
    exercise_name = models.CharField(max_length=200)
    # exercise_type = models.CharField(max_length=100, blank=True, null=True)
    difficulty_level = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    
    # # Exercise parameters (can be customized per prescription)
    # sets = models.IntegerField(default=3)
    # reps = models.IntegerField(default=10)
    # hold_time_sec = models.IntegerField(default=0, help_text="Hold time in seconds for isometric exercises")
    # rest_time_sec = models.IntegerField(default=60, help_text="Rest time between sets in seconds")
    
    # # Additional notes for this specific exercise
    # exercise_notes = models.TextField(blank=True, null=True)
    
    # Order of exercises in the prescription
    order = models.IntegerField(default=0, help_text="Display order of exercises")
    
    # Tracking completion
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescription_exercises'
        ordering = ['order', 'id']
        verbose_name = 'Prescription Exercise'
        verbose_name_plural = 'Prescription Exercises'
        # Prevent duplicate exercises in same position for the same prescription
        unique_together = ['prescription', 'exercise_id_in_library', 'order']
    
    def __str__(self):
        return f"{self.exercise_name}"
    
    # def get_total_reps(self):
    #     """Calculate total repetitions across all sets"""
    #     return self.sets * self.reps
    
    # def get_duration_minutes(self):
    #     """Estimate total duration for this exercise in minutes"""
    #     # Assume 3 seconds per rep, plus rest time between sets
    #     exercise_time = self.reps * 3  # seconds
    #     rest_time = self.rest_time_sec * (self.sets - 1)  # seconds
    #     total_seconds = exercise_time + rest_time
    #     return round(total_seconds / 60, 1)
    
    def mark_completed(self):
        """Mark this exercise as completed"""
        self.is_completed = True
        from django.utils import timezone
        self.completed_at = timezone.now()
        self.save()
    
    def mark_incomplete(self):
        """Mark this exercise as incomplete"""
        self.is_completed = False
        self.completed_at = None
        self.save()
    
    def get_latest_exercise_data(self):
        """Get the latest data from the original exercise in """
        if self.exercise:
            return {
                'name': self.exercise.exercise_name,
                'type': self.exercise.exercise_type,
                'difficulty': self.exercise.difficulty_level,
                'description': getattr(self.exercise, 'exercise_description', '')
            }
        return None
