# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
%define etc_ignite_conf %{_sysconfdir}/%{name}/conf
%define etc_ignite_conf_dist %{etc_ignite_conf}.dist
%define ignite_home /usr/lib/%{name}
%define bin_ignite %{ignite_home}/bin
%define lib_ignite %{ignite_home}/lib
%define conf_ignite %{ignite_home}/config
%define logs_ignite %{ignite_home}/logs
%define pids_ignite %{ignite_home}/pids
%define man_dir %{_mandir}
%define ignite_username ignite
%define ignite_services ignite-hadoop
%define vcs_tag %{ignite_hadoop_version}

%if  %{?suse_version:1}0

# Only tested on openSUSE 11.4. le'ts update it for previous release when confirmed
%if 0%{suse_version} > 1130
%define suse_check \# Define an empty suse_check for compatibility with older sles
%endif

# SLES is more strict anc check all symlinks point to valid path
# But we do point to a hadoop jar which is not there at build time
# (but would be at install time).
# Since our package build system does not handle dependencies,
# these symlink checks are deactivated
%define __os_install_post \
    %{suse_check} ; \
    /usr/lib/rpm/brp-compress ; \
    %{nil}

%define doc_ignite %{_docdir}/%{name}
%global initd_dir %{_sysconfdir}/rc.d
%define alternatives_cmd update-alternatives

%else

# CentOS 5 does not have any dist macro
# So I will suppose anything that is not Mageia or a SUSE will be a RHEL/CentOS/Fedora
%if %{!?mgaversion:1}0

# FIXME: brp-repack-jars uses unzip to expand jar files
# Unfortunately guice-2.0.jar pulled by ivy contains some files and directories without any read permission
# and make whole process to fail.
# So for now brp-repack-jars is being deactivated until this is fixed.
# See BIGTOP-294
#%define __os_install_post \
#    %{_rpmconfigdir}/brp-compress ; \
#    %{_rpmconfigdir}/brp-strip-static-archive %{__strip} ; \
#   %{_rpmconfigdir}/brp-strip-comment-note %{__strip} %{__objdump} ; \
#   /usr/lib/rpm/brp-python-bytecompile ; \
#   %{nil}
%endif

%define doc_ignite %{_docdir}/%{name}-%{ignite_hadoop_version}
%global initd_dir %{_sysconfdir}/rc.d/init.d
%define alternatives_cmd alternatives

%endif


Name: ignite-hadoop
Version: %{ignite_hadoop_version}
Release: %{ignite_hadoop_release}
Summary: Ignite Hadoop accelerator. The system provides for in-memory caching of HDFS data and MR performance improvements
URL: http://ignite.incubator.apache.org/
Group: Development/Libraries
Buildroot: %{_topdir}/INSTALL/%{name}-%{version}
License: APL2
Source0: ignite-hadoop-%{ignite_hadoop_base_version}.tar.gz
Source1: do-component-build
Source2: install_ignite.sh
Source3: ignite-hadoop.svc
Source4: init.d.tmpl
Source5: ignite-hadoop.default
BuildArch: noarch
Requires: coreutils, /usr/sbin/useradd, /sbin/chkconfig, /sbin/service
Requires: hadoop-hdfs, hadoop-mapreduce, bigtop-utils >= 0.7

%if  0%{?mgaversion}
Requires: bsh-utils
%else
Requires: sh-utils
%endif

%description
Ignite is an open-source, distributed, in-memory computation platform

    * HDFS caching and MR performance booster

%package service
Summary: Hadoop Accelerator platform
Group: System/Daemons
Requires: %{name} = %{version}-%{release}
Requires(pre): %{name} = %{version}-%{release}

%if  %{?suse_version:1}0
# Required for init scripts
Requires: insserv
%endif

%if  0%{?mgaversion}
# Required for init scripts
Requires: initscripts
%endif

# CentOS 5 does not have any dist macro
# So I will suppose anything that is not Mageia or a SUSE will be a RHEL/CentOS/Fedora
%if %{!?suse_version:1}0 && %{!?mgaversion:1}0
# Required for init scripts
Requires: redhat-lsb
%endif

%description service
Ignite Hadoop accelerator package

%package doc
Summary: Ignite Documentation
Group: Documentation
BuildArch: noarch

%description doc
Documentation for Ignite platform

%prep
%setup -n ignite-hadoop-%{vcs_tag}

%build
bash %{SOURCE1}

%install
%__rm -rf $RPM_BUILD_ROOT
env IGNITE_HADOOP_VERSION=%{version} bash %{SOURCE2} \
  --build-dir=target/bin \
  --doc-dir=%{doc_ignite} \
  --conf-dir=%{etc_ignite_conf_dist} \
	--prefix=$RPM_BUILD_ROOT

%__install -d -m 0755 $RPM_BUILD_ROOT/%{initd_dir}/

%__install -d -m 0755 $RPM_BUILD_ROOT/etc/default/
%__install -m 0644 %{SOURCE5} $RPM_BUILD_ROOT/etc/default/%{name}

%__install -d  -m 0755  %{buildroot}/%{_localstatedir}/log/%{name}

ln -s %{_localstatedir}/log/%{name} %{buildroot}/%{logs_ignite}

%__install -d  -m 0755  %{buildroot}/%{_localstatedir}/run/%{name}
ln -s %{_localstatedir}/run/%{name} %{buildroot}/%{pids_ignite}

for service in %{ignite_services}
do
    init_file=$RPM_BUILD_ROOT/%{initd_dir}/%{name}
    %__sed -e "s|@IGNITE_DAEMON@|${service}|" %{SOURCE3} > ${RPM_SOURCE_DIR}/ignite.node
    bash %{SOURCE4} ${RPM_SOURCE_DIR}/ignite.node rpm $init_file

    chmod 755 $init_file
done

%__install -d -m 0755 $RPM_BUILD_ROOT/usr/bin

# Pull hadoop from their packages
rm -f $RPM_BUILD_ROOT/%{lib_ignite}/libs/{hadoop}*.jar

%pre
getent group ignite 2>/dev/null >/dev/null || /usr/sbin/groupadd -r ignite
getent passwd ignite 2>&1 > /dev/null || /usr/sbin/useradd -c "ignite" -s /sbin/nologin -g ignite -r -d /var/run/ignite ignite 2> /dev/null || :

%post
%{alternatives_cmd} --install %{etc_ignite_conf} %{name}-conf %{etc_ignite_conf_dist} 30

%preun
if [ "$1" = 0 ]; then
        %{alternatives_cmd} --remove %{name}-conf %{etc_ignite_conf_dist} || :
fi

#######################
#### FILES SECTION ####
#######################
%files
%defattr(-,ignite,ignite)
%dir %{_localstatedir}/log/%{name}
%dir %{_localstatedir}/run/%{name}

%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/default/%{name}
%{ignite_home}
/usr/bin/%{name}
%config(noreplace) %{etc_ignite_conf_dist}

%files doc
%defattr(-,root,root)
%doc %{doc_ignite}/

%define service_macro() \
%files %1 \
%attr(0755,root,root)/%{initd_dir}/%{name} \
%post %1 \
chkconfig --add %{name} \
\
%preun %1 \
if [ $1 = 0 ] ; then \
        service %{name} stop > /dev/null 2>&1 \
        chkconfig --del %{name} \
fi \
%postun %1 \
if [ $1 -ge 1 ]; then \
        service %{name} condrestart >/dev/null 2>&1 \
fi
%service_macro service
