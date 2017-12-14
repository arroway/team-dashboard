# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import date, datetime, timedelta
from libmozdata.bugzilla import Bugzilla
from libmozdata import utils
from time import strftime
import os

class Bugs():
    def __init__(self):
        self.data = {}

    def clear(self):
        self.data = {}

class Metrics():

    SEVERITY_LIST = ['sec-critical', 'sec-high', 'sec-moderate', 'sec-low']

    def __init__(self, severity='', component=''):
        self.measure_datetime = datetime.now()
        self.bugs = Bugs()
        self.severity = severity
        self.component = component

    def clear(self):
        self.bugs = {}
        self.severity = ''
        self.component = ''

    def get_bugs(self, data, keywords='', resolution='', component='', other_params=''):
        """ Use Bugzilla API to get bugs
        """
        def bughandler(bug, data):
            data[bug['id']] = bug

        search_query = 'keywords={0}&resolution={1}&component={2}&{3}'.format(keywords, resolution, component, other_params)
        Bugzilla(search_query, bughandler=bughandler, bugdata=data).get_data().wait()

    def get_metrics(self):

        if self.severity == '' and self.component == '':
            #get bugs for all components at once, and for each severity rate
            for severity in self.SEVERITY_LIST:
                self.bugs.clear()
                self.get_bugs(self.bugs.data, keywords=severity, resolution='---')
                self.compute_metrics(severity)

        # TODO: replace code above to avoid querying Bugzilla again
        else:
            #get bugs for each component, and for each severity rate that is specified
            self.bugs.clear()
            self.get_bugs(self.bugs.data, keywords=self.severity, resolution='---', component=self.component)
            self.compute_metrics(self.severity)

    def compute_metrics(self, severity):

        nb_open = len(self.bugs.data)

        if self.component:
            print '{0} {1} {2} open bugs:'.format(self.component, nb_open, severity.upper())
        else:
            print 'ALL components {0} {1} open bugs'.format(nb_open, severity.upper())

        RELEASES = ['_esr52', '56', '57', '58']

        for release in RELEASES:
            self.bugs.clear()
            self.get_tracked_bugs(release, severity)
            nb_tracked = len(self.bugs.data)

            if nb_tracked > 0:
                # How many bugs tracking a release are not affecting it
                unaffected_status = ['fixed','disabled','unaffected','verified disabled']
                nb_not_affected = self.get_bugcount_with_status(release, unaffected_status)

                # How many bugs tracking a release are actually affecting it
                affected_status = ['?','wontfix','affected','verified','fix-optional']
                nb_affected = self.get_bugcount_with_status(release, affected_status)

                # How many bugs tracking a release are open/closed/.
                nb_open, nb_closed = self.get_open_bugcount(release)

                # Print collected metrics
                # TODO: generate metrics to JSON format
                print '= Firefox {0}: tracked {1} | affected {2} | not affected {3} | open {4} | closed {5}'.format(release, nb_tracked, nb_affected, nb_not_affected, nb_open, nb_closed)
            else:
                print '= Firefox {0}: tracked {1}'.format(release, nb_tracked)

    def get_tracked_bugs(self, release, severity):
        """Get bugs with tracking flag for given release
        """
        resolution = '---&resolution=FIXED'
        f1 ='cf_status_firefox' + release
        o1 = 'anyexact'
        v1 = '?, wontfix,affected,verified,fix-optional,fixed,disabled,unaffected,verified disabled'
        tracking_flags = '&f1=' + f1 + '&o1=' + o1 + '&v1=' + v1
        self.get_bugs(self.bugs.data, keywords=severity, resolution=resolution, component=self.component, other_params=tracking_flags)

    def get_bugcount_with_status(self, release, status):
        """Get bug count depending on status for given release
        """
        count = 0
        flag = 'cf_status_firefox' + release
        for bug in self.bugs.data:
            b = self.bugs.data[bug]
            if flag not in b:
                return -1
            if b[flag] in status:
                count +=1
        return count

    def get_open_bugcount(self, release):
        """Get bug count depending on its resolution state (open/closed)
        """
        nb_open = 0
        nb_closed = 0
        flag = 'cf_status_firefox' + release
        for bug in self.bugs.data:
            b = self.bugs.data[bug]
            if b['is_open']:
                nb_open +=1
            else:
                nb_closed +=1
        return nb_open, nb_closed

if __name__ == "__main__":
    # Get metrics for all components and all severity types
    allbugs = Metrics()
    allbugs.get_metrics()

    SEVERITY_LIST = ['sec-critical', 'sec-high']
    # TODO: automatically get components list from Bugzilla
    # TODO: re-use data retrieved in previous query to avoid duplicatin Bugzilla queries (time consuming)
    COMPONENTS_LIST = ['Audio/Video', 'DOM', 'GFX', 'JavaScript: GC']
    AV = ['Audio/Video', 'Audio/Video: cubeb', 'Audio/Video: GMP', 'Audio/Video: MediaStreamGraph', 'Audio/Video: Playback', 'Audio/Video: Recording']
    DOM = ['DOM', 'DOM: Animation', 'DOM: Content Processes', 'DOM: Core & HTML', 'DOM: CSS Object Model', 'DOM: Device Interfaces', 'DOM: Events', 'DOM: File', 'DOM: Flyweb', 'DOM: IndexedDB']
    # TODO: to be completed...

    for component in AV+DOM:
        for severity in SEVERITY_LIST:
            m = Metrics(severity, component); #todo reuse same object
            m.get_metrics()
        # TODO: agregate metrics for whole component
