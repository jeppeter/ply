#! /usr/bin/env perl -w

use strict;
use Getopt::Long;
use Config::General qw(ParseConfig);
use Data::Dumper;
use Pod::Usage;

my %opts;
my %conf;
my ($verbose)=0;

sub Debug($)
{
	my ($fmt)=shift @_;
	my ($callback)=1;
	my ($p,$f,$l);
	my ($fmtstr)="";
	if (scalar(@_) > 0) {
		$callback = shift @_;
	}
	if ($verbose > 0) {
		if ($verbose >= 3) {
			($p,$f,$l) = caller($callback);
			$fmtstr .= "[$f:$l] ";
		}
		$fmtstr .= $fmt;
		print STDERR $fmtstr."\n";
	}
	return;
}

Getopt::Long::Configure("bundling","no_ignore_case");
Getopt::Long::GetOptions(\%opts,
	"config|c=s",
	"verbose|v+",
	"help|h");

if (defined($opts{'help'})) {
	pod2usage(-extval => 0 ,-verbose => 2);
}

if (defined($opts{'verbose'})) {
	$verbose = $opts{'verbose'};
}

if (!defined($opts{'config'})) {
	pod2usage(-message => "not defined config",
			-extval => 3,
			-verbose => 2,
			-output => \*STDERR);
}

%conf = ParseConfig(-ConfigFile => $opts{'config'},
		-UseApacheInclude => 1,
		-IncludeDirectories => 1, 
		-IncludeGlob => 1, 
		-MergeDuplicateBlocks => 1);

print STDOUT "configuration\n";
print STDOUT Dumper(\%conf);


__END__
=head1 readconf.pl

readconf.pl - Using Config::General qw(ParseConfig)

=head1 SYNOPSIS

readconf.pl [options] 

 Options:
   --help|-h            brief help message
   --config|-c  config  set config file
   --verbose|-v         set verbose mode

=head1 OPTIONS

=over 8

=item B<--help|-h>

Print a brief help message and exits.

=item B<--config|-c>

Specify config file

=back

=head1 DESCRIPTION

B<readconf.pl> will read the given config file and dump

=cut