Name:           RatticWeb
Version:        master
Release:        1%{?dist}
Summary:        RatticWeb is password management for humans.

License:        GPL
URL:            http://rattic.org/
Source0:        https://github.com/tildaslash/%{name}/archive/%{version}.tar.gz
Source1:        RatticWeb.pybundle

BuildArch:      noarch

BuildRequires:  python httpd mod_wsgi mod_ssl
BuildRequires:  python-pip python-virtualenv openldap-devel mysql-devel

Requires:       python httpd mod_wsgi mod_ssl openldap mysql

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
rm Vagrantfile

# Copy RatticWeb into place
mkdir -p %{buildroot}/opt/apps/Rattic/web
cp -av . %{buildroot}/opt/apps/Rattic/web/

# Install dependencies
mkdir -p %{buildroot}/opt/apps/RatticWeb/venv
virtualenv %{buildroot}/opt/apps/RatticWeb/venv
source %{buildroot}/opt/apps/RatticWeb/venv/bin/activate
pip install %{SOURCE1}

# Test
cd %{buildroot}/opt/apps/Rattic/web/
source %{buildroot}/opt/apps/RatticWeb/venv/bin/activate
./manage.py test

%files
/opt/apps/Rattic/*
%doc README.md

%changelog
