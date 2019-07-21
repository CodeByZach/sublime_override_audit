import sublime
import sublime_plugin

from ..core import oa_syntax, oa_setting, decorate_pkg_name, log
from ..core import packages_with_overrides, ReportGenerationThread
from ...lib.packages import PackageList, OverrideDiffResult



class BulkDiffReportThread(ReportGenerationThread):
	"""
	Perform a bulk diff of all overrides in either all packages or a single
	package, depending on the argument provided.

	This is invoked from OverrideAuditDiffOverride when you invoke that command
	with the bulk argument set to true.
	"""
	def _process(self):
		package = self.args["package"]
		force_reuse = self.args["force_reuse"]

		pkg_list = PackageList(package)

		if package is not None:
			if package not in pkg_list:
				return log("Cannot diff package '%s'; not found" % package,
							status=True, dialog=True)

			items = [package]
		else:
			items = packages_with_overrides(pkg_list)

		self._diff_packages(items, pkg_list, package is not None, force_reuse)

	def _diff_packages(self, names, pkg_list, single_package, force_reuse):
		context_lines = oa_setting("diff_context_lines")
		binary_patterns = oa_setting("binary_file_patterns")

		result = []
		title = "Override Diff Report: "
		description = "Bulk Diff Report for overrides in"
		report_type = ":bulk_all"
		expired_pkgs = []
        unknown_files = {}

		if len(names) == 1 and single_package:
			title += names[0]
			result.append(description + " {}\n".format(names[0]))
			report_type = names[0]
		elif len(names) == 0:
			title += "All Packages"
			result.append("No packages with overrides found to diff\n")
		else:
			title += "All Packages"
			result.append(description + " {} packages\n".format(len(names)))

		result.append(self._generation_time())

		for name in names:
			pkg_info = pkg_list[name]
			if binary_patterns is not None:
				pkg_info.set_binary_pattern(binary_patterns)

			result.append(decorate_pkg_name(pkg_info))
			self._perform_diff(pkg_info, context_lines, result,
                               expired_pkgs, unknown_files)

		self._set_content(title, result, report_type, oa_syntax("OA-Diff"),
                          {
                            "override_audit_expired_pkgs": expired_pkgs,
                            "override_audit_unknown_overrides": unknown_files
                          })

    def _perform_diff(self, pkg_info, context_lines, result, expired_pkgs, unknown_files):
        pkg_files = pkg_info.unpacked_contents()
		override_list = pkg_info.override_files(simple=True)
		expired_list = pkg_info.expired_override_files(simple=True)
        unknown_overrides = pkg_info.unknown_override_files()

		empty_diff_hdr = oa_setting("diff_empty_hdr")

		if expired_list:
			expired_pkgs.append(pkg_info.name)

        if unknown_overrides:
            unknown_files[pkg_info.name] = list(unknown_overrides)

        for file in pkg_files:
			if file in expired_list:
				result.append("    [X] {}".format(file))
            elif file in unknown_overrides:
                result.append("    [?] {}".format(file))
			else:
				result.append("    {}".format(file))

            if file in unknown_overrides:
                diff = OverrideDiffResult(None, None, (" " * 8) +
                                          "<File does not exist in the underlying package file; cannot diff>")
            else:
			diff = pkg_info.override_diff(file, context_lines,
										  empty_result="No differences found",
										  binary_result="<File is binary>",
										  indent=8)

			if diff is None:
				content = (" " * 8) + ("Error opening or decoding file;"
									   " is it UTF-8 or Binary?")
			else:
				prefix = diff.hdr if diff.is_empty and empty_diff_hdr else ""
				content = prefix + diff.result

			result.extend([content, ""])

        if not override_list and not unknown_overrides:
			if pkg_info.has_possible_overrides(simple=True):
				result.append("    <No simple overrides found>")
			else:
				reason = ("no sublime-package" if pkg_info.is_unpacked() else
						  "no unpacked files")
				result.append("    <No overrides possible; %s>" % reason)
		result.append("")



class OverrideAuditDiffReportCommand(sublime_plugin.WindowCommand):
	"""
	Perform a bulk diff of all overrides in either all packages or a single
	package, depending on the argument provided.

	This is invoked from OverrideAuditDiffOverride when you invoke that command
	with the bulk argument set to true.
	"""
	def run(self, package=None, force_reuse=False):
		BulkDiffReportThread(self.window, "Generating Bulk Diff",
							 self.window.active_view(),
							 package=package, force_reuse=force_reuse).start()
