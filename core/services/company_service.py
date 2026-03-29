


def create_company(user, form):
    company = form.save(commit=False)
    company.owner = user
    company.save()
    return company