Name:           RatticWeb
Version:        master
Release:        1%{?dist}
Summary:        RatticWeb is password management for humans.

License:        GPL
URL:            http://rattic.org/
Source0:        https://github.com/tildaslash/%{name}/archive/%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python Django14 Django-south httpd mod_wsgi mod_ssl MySQL-python
BuildRequires:  python-mimeparse python-six python-crypto
BuildRequires:  python-pip
Requires:       python Django14 Django-south httpd mod_wsgi mod_ssl MySQL-python
BuildRequires:  python-mimeparse python-six python-crypto

%description


%prep
%setup -qn %{name}-%{version}

%check

%build

%install
# Cleanup
rm -rf %{buildroot}

# Remove things we don't want to package
rm .gitignore
rm .travis.yml

# Copy RatticWeb into place
mkdir -p %{buildroot}/opt/apps/RatticWeb
cp -av . %{buildroot}/opt/apps/RatticWeb

# Install dependencies
mkdir -p %{buildroot}/opt/apps/RatticWeb-pip/
pip-python install --install-option="--prefix=%{buildroot}/opt/apps/RatticWeb-pip/" django-tastypie
pip-python install --install-option="--prefix=%{buildroot}/opt/apps/RatticWeb-pip/" markdown

# Test
cd %{buildroot}/opt/apps/RatticWeb
export PYTHONPATH=%{buildroot}/opt/apps/RatticWeb-pip/lib/python2.6/site-packages/
./manage.py test

%files
/opt/apps/RatticWeb/*
/opt/apps/RatticWeb-pip/*
%doc README.md

%changelog
