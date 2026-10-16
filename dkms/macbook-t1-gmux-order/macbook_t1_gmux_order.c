// SPDX-License-Identifier: GPL-2.0
/*
 * Resume the Apple gmux before i915 on MacBookPro13,3.
 *
 * After S3 the gmux DDC/AUX switch points at the discrete GPU until
 * apple-gmux's resume callback restores it. Nothing orders that callback
 * before i915's, so i915 resumed first and every eDP AUX transfer timed out
 * (about 350 timeouts, 4.7 s of black screen). A device link with gmux as
 * supplier makes the PM core resume gmux first and suspend it last.
 */

#include <linux/acpi.h>
#include <linux/device.h>
#include <linux/dmi.h>
#include <linux/module.h>
#include <linux/pci.h>

static struct device_link *link;
static struct pci_dev *igpu;
static struct device *gmux;

static const struct dmi_system_id macbook_t1_gmux_order_dmi[] = {
	{
		.ident = "Apple MacBookPro13,3",
		.matches = {
			DMI_MATCH(DMI_SYS_VENDOR, "Apple Inc."),
			DMI_MATCH(DMI_PRODUCT_NAME, "MacBookPro13,3"),
		},
	},
	{}
};
MODULE_DEVICE_TABLE(dmi, macbook_t1_gmux_order_dmi);

static int __init macbook_t1_gmux_order_init(void)
{
	struct acpi_device *adev;

	if (!dmi_check_system(macbook_t1_gmux_order_dmi))
		return -ENODEV;

	adev = acpi_dev_get_first_match_dev("APP000B", NULL, -1);
	if (!adev)
		return -ENODEV;
	gmux = get_device(acpi_get_first_physical_node(adev));
	acpi_dev_put(adev);
	if (!gmux || !gmux->driver) {
		pr_err("apple-gmux device not bound\n");
		put_device(gmux);
		return -EPROBE_DEFER;
	}

	igpu = pci_get_domain_bus_and_slot(0, 0, PCI_DEVFN(2, 0));
	if (!igpu) {
		put_device(gmux);
		return -ENODEV;
	}

	link = device_link_add(&igpu->dev, gmux, DL_FLAG_STATELESS);
	if (!link) {
		pci_dev_put(igpu);
		put_device(gmux);
		return -EINVAL;
	}
	pci_info(igpu, "resume ordered after %s\n", dev_name(gmux));
	return 0;
}

static void __exit macbook_t1_gmux_order_exit(void)
{
	device_link_del(link);
	pci_dev_put(igpu);
	put_device(gmux);
}

module_init(macbook_t1_gmux_order_init);
module_exit(macbook_t1_gmux_order_exit);

MODULE_AUTHOR("MacBookPro13,3 Omarchy support kit");
MODULE_DESCRIPTION("Resume Apple gmux before i915 on MacBookPro13,3");
MODULE_LICENSE("GPL");
MODULE_SOFTDEP("pre: apple_gmux");
