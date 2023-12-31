from typing import Any

import requests
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q, QuerySet
from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView, View

from .forms import AddBookByIsbnForm, BookSearchForm
from .models import Book, Author
from pprint import pprint



# Create your views here.
class BookListView(ListView):
    model = Book
    context_object_name = "books"
    template_name = "books/list.html"

    def get_queryset(self) -> QuerySet[Any]:
        if self.request.GET:
            lookup = BookSearchForm(self.request.GET)
            # search book by title and author
            if lookup.is_valid():
                print(lookup)
                query = lookup.cleaned_data["q"].split(" ")
                qset = Q()
                for q in query:
                    qset |= (
                        Q(title__icontains=q)
                        | Q(author__names__icontains=q)
                        | Q(isbn__exact=q)
                    )
                return Book.objects.filter(qset)
        else:
            return super().get_queryset()


class BookDetailView(DetailView):
    model = Book
    context_object_name = "book"
    template_name = "books/detail.html"


class AddBookByIsbn(PermissionRequiredMixin, View):
    permission_required = "books.book.can_add_book"
    form_class = AddBookByIsbnForm
    template_name = "books/add.html"

    def post(self, request, *args, **kwargs):
        form = AddBookByIsbnForm(self.request.POST)
        if form.is_valid():
            isbn_list = form.cleaned_data["isbn_list"]
            isbn_list = isbn_list.replace('\r', '').split("\n")
            for isbn in isbn_list:
                url = f"https://openlibrary.org/isbn/{isbn}.json"
                resp = requests.get(url)
                not_found = []
                if resp.status_code is not 400:
                    book = resp.json()
                    # author = Author.objects.get_or_create(open_library_key=book.auth)
                    pprint(book)
                else:
                    not_found.append(isbn)
                    pprint(not_found)

            return redirect(reverse('add_by_isbn'))
        else:
            return render(request, self.template_name, context={'form':form})
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    