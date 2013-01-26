from __future__ import print_function
import os
import sys
import sh
import itertools
import absence.secrets as secrets
import absence.sendmail as sendmail

class DuplicityDriver(object):

    def __init__(self, duplicity_cmd, secrets_cfg, mailer):
        self.secrets = secrets_cfg
        self._stderr = []
        self.mailer = mailer
        self.duplicity = duplicity_cmd
        self.send_email = True
        self.set_environment(
            self.secrets.get('s3', 'AWS_ACCESS_KEY_ID'),
            self.secrets.get('s3', 'AWS_SECRET_ACCESS_KEY'),
            self.secrets.get('gpg', 'passphrase'))

    def backup_to(self, destination):
        options = (['--allow-source-mismatch',
                    '--full-if-older-than', '30D']
                    + self.includes
                    + ['--exclude', '**', os.environ['HOME'], destination])
        return self.execute(*options)

    def execute(self, *options):
        try:
            options = self.gpg_key + self.archive + list(options)
            return self.duplicity(*options, _err=self._save_stderr).wait()
        except sh.ErrorReturnCode:
            options_str = '\n'.join(options)
            body = self._show_stderr() + '\n' +  options_str
            if self.send_email:
                self.mailer.sendmail([self.secrets.get('mail', 'user')],
                                     body, '"absence" failed')
            else:
                print(body)
            return None
        
    def backup(self):
        for destination in self.destinations:
            print('Sending to {}...'.format(destination), end=' ')
            sys.stdout.flush()
            cmd = self.backup_to(destination)
            print('done' if cmd is not None else 'failed')

    def check(self, destination):
        return self.execute('collection-status', destination).stdout

    def list_files(self, destination):
        return self.execute('list-current-files', destination).stdout

    def restore(self, from_destination, to_directory):
        return self.execute('restore', from_destination, to_directory)
        
    def _save_stderr(self, line):
        self._stderr.append(line)

    def _show_stderr(self):
        return ''.join(self._stderr)

    @property
    def gpg_key(self):
        return ['--encrypt-key', self.secrets.get('gpg', 'key')]

    @property
    def archive(self):
        return ['--archive-dir', '{}/.cache/duplicity'.format(secrets.DIRECTORY)]

    @property
    def includes(self):
        return list(itertools.chain(('--include', source) for source in self.sources))

    @property
    def sources(self):
        home = self.secrets.get('duplicity', 'home')
        return [os.path.join(home, source)
                for source in self.secrets.get('duplicity', 'sources').split()]

    @property
    def destinations(self):
        return self.secrets.get('duplicity', 'destinations').split()
    
    def set_environment(self, key_id, secret_key, passphrase):
        os.environ['AWS_ACCESS_KEY_ID'] = key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        os.environ['PASSPHRASE'] = passphrase

    def close(self):
        self.set_environment('', '', '')


def create_driver():
    return DuplicityDriver(sh.duplicity, secrets.read(), sendmail.create_mailer())