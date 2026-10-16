// SPDX-License-Identifier: GPL-2.0
/*
 * Tell the MacBookPro13,3 T1 that the host is awake after system sleep.
 *
 * In S3 the T1 is told the host sleeps and keeps the Touch Bar dark until
 * ASOC.SOCW(1) sends the wake message through the EC mailbox, as macOS does.
 * The apple-ibridge driver skips SOCW on this model because it hard-locked a
 * MacBookPro14,3 during probe, so this module only calls it after resume.
 */

#include <linux/acpi.h>
#include <linux/dmi.h>
#include <linux/module.h>
#include <linux/suspend.h>

#define ASOC_SOCW "\\_SB.PCI0.XHC1.RHUB.ASOC.SOCW"

static bool wake_now;
module_param(wake_now, bool, 0444);
MODULE_PARM_DESC(wake_now, "Call SOCW(1) once at load time (testing)");

static acpi_handle socw;

static const struct dmi_system_id macbook_t1_socw_dmi[] = {
	{
		.ident = "Apple MacBookPro13,3",
		.matches = {
			DMI_MATCH(DMI_SYS_VENDOR, "Apple Inc."),
			DMI_MATCH(DMI_PRODUCT_NAME, "MacBookPro13,3"),
		},
	},
	{}
};
MODULE_DEVICE_TABLE(dmi, macbook_t1_socw_dmi);

static void macbook_t1_socw_wake(void)
{
	unsigned long long result = 0;
	union acpi_object arg = { .integer = { .type = ACPI_TYPE_INTEGER, .value = 1 } };
	struct acpi_object_list args = { .count = 1, .pointer = &arg };
	acpi_status status;

	status = acpi_evaluate_integer(socw, NULL, &args, &result);
	if (ACPI_FAILURE(status))
		pr_warn("SOCW(1) failed: %s\n", acpi_format_exception(status));
	else
		pr_info("SOCW(1) sent T1 wake, result %llu\n", result);
}

static int macbook_t1_socw_pm(struct notifier_block *nb, unsigned long action,
			      void *data)
{
	if (action == PM_POST_SUSPEND)
		macbook_t1_socw_wake();
	return NOTIFY_DONE;
}

static struct notifier_block macbook_t1_socw_nb = {
	.notifier_call = macbook_t1_socw_pm,
};

static int __init macbook_t1_socw_init(void)
{
	if (!dmi_check_system(macbook_t1_socw_dmi))
		return -ENODEV;
	if (ACPI_FAILURE(acpi_get_handle(NULL, ASOC_SOCW, &socw))) {
		pr_err("%s not found\n", ASOC_SOCW);
		return -ENODEV;
	}
	if (wake_now)
		macbook_t1_socw_wake();
	return register_pm_notifier(&macbook_t1_socw_nb);
}

static void __exit macbook_t1_socw_exit(void)
{
	unregister_pm_notifier(&macbook_t1_socw_nb);
}

module_init(macbook_t1_socw_init);
module_exit(macbook_t1_socw_exit);

MODULE_AUTHOR("MacBookPro13,3 Omarchy support kit");
MODULE_DESCRIPTION("Send the T1 its host-wake message after system sleep");
MODULE_LICENSE("GPL");
