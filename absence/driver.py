from __future__ import print_function

import itertools
import os
import sys

import absence.secrets as secrets
import absence.sendmail as sendmail
import sh

class DuplicityDriver(object):

    def __init__(self, duplicity_cmd, secrets_cfg, mailer, archive_dir):
        self.secrets = secrets_cfg
        self._stderr = []
        self.mailer = mailer
        self.duplicity = duplicity_cmd
        self.archive_dir = archive_dir
        self.send_email = (self.secrets.getboolean('duplicity', 'mail')
                           if self.secrets.has_option('duplicity', 'mail')
                           else False)
        self.set_environment(
            self.secrets.get('s3', 'AWS_ACCESS_KEY_ID'),
            self.secrets.get('s3', 'AWS_SECRET_ACCESS_KEY'),
            self.secrets.get('gpg', 'passphrase'),
            self.secrets.get('ftp', 'password'))

    def test_mail(self):
        to = self.secrets.get('mail', 'user')
        self.mailer.sendmail([to],
                             'This is a test mail from the backup system.',
                             subject='test mail from backup system')
        return to
        
    def backup_to(self, destination, debug=False):
        self.check_sources()
        options = (['--allow-source-mismatch',
                    '--full-if-older-than', '30D']
                    + self.includes
                    + ['--exclude', '**', '/', destination])
        if debug:
            options.insert(0, '-v9')
        return self.execute(*options)

    def execute(self, *options):
        try:
            options = self.gpg_homedir + self.gpg_key + self.archive + list(options)
            return self.duplicity(*options, _err=self._save_stderr, _out=sys.stdout, _out_bufsize=0).wait()
        except sh.ErrorReturnCode:
            options_str = '\n'.join(map(str, options))
            body = self._show_stderr() + '\n' +  options_str
            print('\n*** ERROR ***\n')
            print(body)
            if self.send_email:
                print('\n*** Will send email ***\n')
                self.mailer.sendmail([self.secrets.get('mail', 'user')],
                                     body, '"absence" failed')
            return None
        
    def backup(self):
        for destination in self.destinations:
            print('Sending to {}...'.format(destination), end=' ')
            sys.stdout.flush()
            cmd = self.backup_to(destination)
            print('done' if cmd is not None else 'failed')

    def check(self, destination):
        return self.execute('collection-status', destination).stdout

    def check_sources(self):
        """Check all sources exist."""
        for source in self.sources:
            if not os.path.exists(source):
                print('------')
                print('Warning: source {0} does not exist'.format(source))
                print('------')
        
    def list_files(self, destination):
        return self.execute('list-current-files', destination).stdout

    def remove(self, destination, older_than):
        return self.execute('remove-older-than', '--num-retries=1', older_than, '--force', destination).stdout
        
    def restore(self, from_destination, to_directory, relpath=None):
        options = ['restore', from_destination, to_directory]
        if relpath is not None:
            options[1:1] = ['--file-to-restore', relpath]
        return self.execute(*options)

    def cleanup(self, destination):
        return self.execute('cleanup', '--force', '--extra-clean', destination).stdout
        
    def _save_stderr(self, line):
        self._stderr.append(line)

    def _show_stderr(self):
        return ''.join(self._stderr)

    @property
    def gpg_key(self):
        return ['--encrypt-key', self.secrets.get('gpg', 'key')]

    @property
    def gpg_homedir(self):
        homedir = self.secrets.get('gpg', 'homedir')
        if homedir is not None:
            return ['--gpg-options', '--homedir={}'.format(homedir)]
        else:
            return []

    @property
    def archive(self):
        return ['--archive-dir', '{}/.cache/duplicity'.format(self.archive_dir)]

    @property
    def includes(self):
        return list(itertools.chain.from_iterable(('--include', source) for source in self.sources))

    @property
    def sources(self):
        home = self.secrets.get('duplicity', 'home')
        key = lambda src: os.path.basename(src.lower())
        return sorted(
            [os.path.join(home, source)
             for source in self.secrets.get('duplicity', 'sources').splitlines()],
            key=key)

    @property
    def destinations(self):
        return self.secrets.get('duplicity', 'destinations').split()
    
    def set_environment(self, key_id, secret_key, passphrase, ftp_password):
        os.environ['AWS_ACCESS_KEY_ID'] = key_id or ''
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key or ''
        os.environ['PASSPHRASE'] = passphrase or ''
        os.environ['FTP_PASSWORD'] = ftp_password or ''

    def close(self):
        self.set_environment('', '', '')


def create_driver(configdir):
    return DuplicityDriver(sh.duplicity, secrets.read(configdir),
                           sendmail.create_mailer(configdir), configdir)

