from jeeves.jobs import *


def test_get_jenkins_job_info():
	pass


def test_get_jenkins_jobs():
	pass


def test_get_osp_version():
	filter_version = r'1{1}[0,3,6]{1}\.{1}\d{1}|1{1}[0,3,6]{1}(?=\D+)'

	assert get_osp_version('DFG-enterprise-baremetal-13.0_director-3control_2compute-titancluster', None) == '13'
	assert get_osp_version('DFG-enterprise-baremetal-13.0_director-3control_2compute-titancluster', False) == '13'
	assert get_osp_version('DFG-enterprise-baremetal-13.0_director-3control_2compute-titancluster', '') == '13'
	assert get_osp_version('DFG-enterprise-baremetal-13.0_director-3control_2compute-titancluster') == '13'
	assert get_osp_version('DFG-all-unified-16_director-rhel-virthost-3cont_2comp_3ceph-ipv4-geneve-ceph-native-default') == '16'
	assert get_osp_version('DFG-ceph-rhos-16.1_director-rhel-virthost-3cont_2comp_3ceph-ipv4-geneve-monolithic') == '16.1'
	assert get_osp_version('DFG-upgrades-updates-from-13-to-16.2-passed_phase1-HA-ipv4') == '16.2'
	assert get_osp_version('DFG-all-unified-16_director-rhel-virthost-3cont_2comp_3ceph-ipv4-geneve-ceph-native-default', filter_version) == '16'
	assert get_osp_version('DFG-backup-restore-overcloud-OSP-16-3cont_2comp_3ceph-ipv4-monolithic-broken-node', filter_version) == '16'
	assert get_osp_version('DFG-ceph-rhos-16_director-rhel-virthost-3cont_2comp_3ceph-ipv4-geneve-monolithic', filter_version) == '16'
	assert get_osp_version('DFG-ceph-rhos-16.1_director-rhel-virthost-3cont_2comp_3ceph-ipv4-geneve-monolithic', filter_version) == '16.1'
	assert get_osp_version('DFG-compute-nova-16_director-rhel-virthost-1cont_2comp_1ipa-ipv4-geneve-tls-everywhere', filter_version) == '16'
	assert get_osp_version('DFG-enterprise-backup_restore-undercloud-controllers-16-3cont_2comp_3ceph-ipv4-rear', filter_version) == '16'
	assert get_osp_version('DFG-enterprise-baremetal-16.2_director-3control_2compute_externalceph-titancluster', filter_version) == '16.2'
	assert get_osp_version('DFG-df-deployment-16-virthost-3cont_2comp_3ceph-ceph-ipv4-geneve-overcloud-ssl-enable', filter_version) == '16'
	assert get_osp_version('DFG-hardware_provisioning-rqci-16_director-rhel-8.1-spineleaf-provision-network-20191605-2117', filter_version) == '16'
	assert get_osp_version('DFG-network-networking-ovn-16_director-rhel-virthost-3cont_2comp-ipv6-geneve', filter_version) == '16'
	assert get_osp_version('DFG-osasinfra-shiftstack_on_vms-16_director-rhel-virthost-3cont_1comp-ipv4-geneve-hybrid_flat_4.3_3master_3worker-ovn', filter_version) == '16'
	assert get_osp_version('DFG-pidone-sanity-16_director-rhel-virthost-3cont_2comp-ipv4-geneve-tobiko_faults-sanity', filter_version) == '16'
	assert get_osp_version('DFG-security-keystone-16_director-rhel-virthost-1cont_1comp-ipv4-geneve-lvm-containers', filter_version) == '16'
	assert get_osp_version('DFG-upgrades-updates-16-from-passed_phase1-HA-ipv4', filter_version) == '16'
	assert get_osp_version('DFG-upgrades-updates-from-13-to-16.2-passed_phase1-HA-ipv4', filter_version) == '16.2'
	assert get_osp_version('DFG-enterprise-baremetal-13.0_director-3control_2compute-titancluster', filter_version) == '13'
	assert get_osp_version('DFG-upgrades-updates-from-osp13.0-to-osp16.2-passed_phase1-HA-ipv4', filter_version) == '16.2'
	assert get_osp_version('DFG-all-unified-weekly-multijob', filter_version) is None
