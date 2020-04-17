from functions import *


def test_get_osp_version_func():
	assert get_osp_version('DFG-all-unified-16_director-rhel-virthost-3cont_2comp_3ceph-ipv4-geneve-ceph-native-default') == '16'
	assert get_osp_version('DFG-backup-restore-overcloud-OSP-16-3cont_2comp_3ceph-ipv4-monolithic-broken-node') == '16'
	assert get_osp_version('DFG-ceph-rhos-16_director-rhel-virthost-3cont_2comp_3ceph-ipv4-geneve-monolithic') == '16'
	assert get_osp_version('DFG-ceph-rhos-16.1_director-rhel-virthost-3cont_2comp_3ceph-ipv4-geneve-monolithic') == '16.1'
	assert get_osp_version('DFG-compute-nova-16_director-rhel-virthost-1cont_2comp_1ipa-ipv4-geneve-tls-everywhere') == '16'
	assert get_osp_version('DFG-enterprise-backup_restore-undercloud-controllers-16-3cont_2comp_3ceph-ipv4-rear') == '16'
	assert get_osp_version('DFG-df-deployment-16-virthost-3cont_2comp_3ceph-ceph-ipv4-geneve-overcloud-ssl-enable') == '16'
	assert get_osp_version('DFG-hardware_provisioning-rqci-16_director-rhel-8.1-spineleaf-provision-network-20191205-2116') == '16'
	assert get_osp_version('DFG-network-networking-ovn-16_director-rhel-virthost-3cont_2comp-ipv6-geneve') == '16'
	assert get_osp_version('DFG-osasinfra-shiftstack_on_vms-16_director-rhel-virthost-3cont_1comp-ipv4-geneve-hybrid_flat_4.3_3master_3worker-ovn') == '16'
	assert get_osp_version('DFG-pidone-sanity-16_director-rhel-virthost-3cont_2comp-ipv4-geneve-tobiko_faults-sanity') == '16'
	assert get_osp_version('DFG-security-keystone-16_director-rhel-virthost-1cont_1comp-ipv4-geneve-lvm-containers') == '16'
	assert get_osp_version('DFG-upgrades-updates-16-from-passed_phase1-HA-ipv4') == '16'
	assert get_osp_version('DFG-all-unified-weekly-multijob') is None


def test_percent_func():
	assert percent(0, 1) == 0.0
	assert percent(1, 2) == 50.0
	assert percent(1, 1) == 100.0
