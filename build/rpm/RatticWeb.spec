Name:           RatticWeb
Version:        master
Release:        1%{?dist}
Summary:        RatticWeb is password management for humans.

License:        GPL
URL:            http://rattic.org/
Source0:        https://github.com/tildaslash/%{name}/archive/%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python Django Django-south
Requires:       python Django14 Django-south

%description


%prep
%setup -qn %{name}-%{version}


%build

%install
rm -rf %{buildroot}
rm .gitignore
rm .travis.yml
mkdir -p %{buildroot}/opt/apps/RatticWeb
cp -av . %{buildroot}/opt/apps/RatticWeb

%files
/opt/apps/RatticWeb/*
%doc



%changelog
