from __future__ import print_function
import os
import sh
import itertools
import absence.secrets as secrets

class DuplicityDriver(object):

    def __init__(self):
        self.secrets = secrets.read()
        self._stderr = []
        self.set_environment(
            self.secrets.get('s3', 'AWS_ACCESS_KEY_ID'),
            self.secrets.get('s3', 'AWS_SECRET_ACCESS_KEY'),
            self.secrets.get('gpg', 'passphrase'))

    def backup(self):
        includes = itertools.chain(('--include', source) for source in self.sources())
        for destination in self.destinations():
            print('Sending to {}...'.format(destination), end=' ')
            options = (['--xarchive-dir', '{}/.cache/duplicity'.format(secrets.DIRECTORY),
                        '--encrypt-key', self.secrets.get('gpg', 'key'),
                        '--full-if-older-than', '30D']
                        + list(includes)
                        + ['--exclude', '**', os.environ['HOME'], destination])
            try:
                sh.duplicity(*options, _err=self._save_stderr).wait()
                print('done')
            except sh.ErrorReturnCode:
                print('failed')
                print(self._show_stderr())

    def _save_stderr(self, line):
        self._stderr.append(line)

    def _show_stderr(self):
        return ''.join(self._stderr)
        
    def sources(self):
        return self.secrets.get('duplicity', 'sources').split()

    def destinations(self):
        return self.secrets.get('duplicity', 'destinations').split()
    
    def set_environment(self, key_id, secret_key, passphrase):
        os.environ['AWS_ACCESS_KEY_ID'] = key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        os.environ['PASSPHRASE'] = passphrase

    def close(self):
        self.set_environment('', '', '')
