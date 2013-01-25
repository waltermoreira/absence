from __future__ import print_function
import os
import sh
import itertools
import absence.secrets as secrets
import absence.sendmail as sendmail

class DuplicityDriver(object):

    def __init__(self):
        self.secrets = secrets.read()
        self._stderr = []
        self.mailer = sendmail.create_mailer()
        self.send_email = True
        self.set_environment(
            self.secrets.get('s3', 'AWS_ACCESS_KEY_ID'),
            self.secrets.get('s3', 'AWS_SECRET_ACCESS_KEY'),
            self.secrets.get('gpg', 'passphrase'))

    def backup_to(self, destination):
        print('Sending to {}...'.format(destination))
        options = (['--archive-dir', '{}/.cache/duplicity'.format(secrets.DIRECTORY),
                    '--allow-source-mismatch',
                    '--full-if-older-than', '30D']
                    + self.gpg_key()
                    + self.includes()
                    + ['--exclude', '**', os.environ['HOME'], destination])
        return self.execute(*options)

    def execute(self, *options):
        try:
            return sh.duplicity(*options, _err=self._save_stderr).wait()
        except sh.ErrorReturnCode:
            options_str = '\n'.join(options)
            body = self._show_stderr() + '\n' +  options_str
            if self.send_email:
                self.mailer.sendmail([self.secrets.get('mail', 'user')],
                                     body, '"absence" failed')
            else:
                print(body)
            
    def gpg_key(self):
        return ['--encrypt-key', self.secrets.get('gpg', 'key')]

    def backup(self):
        for destination in self.destinations():
            self.backup_to(destination)

    def check(self, destination):
        options = self.gpg_key() + ['collection-status', destination]
        return self.execute(*options).stdout

    def list_files(self, destination):
        options = self.gpg_key() + ['list-current-files', destination]
        return self.execute(*options).stdout
            
    def _save_stderr(self, line):
        self._stderr.append(line)

    def _show_stderr(self):
        return ''.join(self._stderr)

    def includes(self):
        return list(itertools.chain(('--include', source) for source in self.sources()))
        
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
