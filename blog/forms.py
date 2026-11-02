from django import forms

from .models import Blog


class BlogForm(forms.ModelForm):
    """Форма создания/редактирования статьи.

    Поле likes намеренно не входит в форму: лайки меняются только
    логикой просмотра, пользователь не может задать их через POST.
    """

    class Meta:
        model = Blog
        fields = ["title", "content"]
