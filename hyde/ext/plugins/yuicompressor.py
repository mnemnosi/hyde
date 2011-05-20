# -*- coding: utf-8 -*-
"""
YUICompressor plugin
"""

import traceback
import subprocess

from hyde.plugin import CLTransformer
from hyde.fs import File

class YUICompressorPlugin(CLTransformer):
    """
    The plugin class for the YUI JavaScript and CSS Compressor
    """

    def __init__(self, site):
        super(YUICompressorPlugin, self).__init__(site)

    @property
    def plugin_name(self):
        """
        The name of the plugin.
        """
        return "yuicompressor"

    @property
    def jar_not_found_message(self):
        """
        Message to be displayed if the JAR is not found.
        """

        return ("%(name)s jar path not configured properly. "
        "This plugin expects `%(name)s.jar` to point "
        "to the `%(name)s` file." % {"name": self.plugin_name})

    @property
    def jar(self):
        """
        The location of the YUI Compressor JAR
        """
        try:
            jar_path = getattr(self.settings, 'jar')
        except AttributeError:
            raise self.template.exception_class(
                    self.jar_not_found_message)

        jar = File(jar_path)

        if not jar.exists:
            raise self.template.exception_class(
                    self.jar_not_found_message)

        return jar

    def text_resource_complete(self, resource, text):
        """
        If the site is in development mode, just return.
        Otherwise, save the file to a temporary place
        and run the uglify app. Read the generated file
        and return the text as output.
        """

        try:
            mode = self.site.config.mode
        except AttributeError:
            mode = "production"

        if resource.source_file.kind not in ('js', 'css'):
            return

        if mode.startswith('dev'):
            self.logger.debug("Skipping yuicompressor in development mode.")
            return

        supported = [
            "charset",
            "line-break",
        ]

        if resource.source_file.kind == "js":
            supported.extend([
                "nomunge",
                "preserve-semi",
                "disable-optimizations"
            ])

        source = File.make_temp(text)
        target = File.make_temp('')
        args = [str(self.app), "-jar", str(self.jar), "--type", resource.source_file.kind]
        args.extend(self.process_args(supported))
        args.extend(["-o", str(target), str(source)])

        self.call_app(args, resource)

        out = target.read_all()
        return out

    def call_app(self, args, resource):
        """
        Calls the application with the given command line parameters.
        """
        try:
            self.logger.debug(
                "Calling executable [%s] with arguments %s for resource %s" %
                    (args[0], str(args[1:]), resource.source_file))
            subprocess.check_call(args)
        except subprocess.CalledProcessError, error:
            self.logger.error(traceback.format_exc())
            self.logger.error(error.output)
            raise