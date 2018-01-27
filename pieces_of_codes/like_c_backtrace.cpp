
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <execinfo.h>
#include <errno.h>
#include <cxxabi.h>
 
static inline void
backtrace_for_cpp( FILE *out = stderr, unsigned int max_frames = 63 )
{
	// storage array for stack trace address data
	void* addr_list[max_frames+1];
	char funcname[1024];
	size_t funcnamesize = 0;

	// retrieve current stack addresses
	unsigned int addr_num = backtrace( addr_list, sizeof( addr_list ) / sizeof( void* ));
	
	if ( addr_num == 0 )
	{
		fprintf( out, "  \n" );
		return;
	}
 
	// resolve addresses into strings containing "filename(function+address)",
	// Actually it will be ## program address function + offset
	// this array must be free()-ed
	char** symbollist = backtrace_symbols( addr_list, addr_num );

	// iterate over the returned symbol lines.
	for ( unsigned int i = 0; i < addr_num; i++ )
	{
		char* begin_name   = NULL;
		char* begin_offset = NULL; // option
		char* end_offset   = NULL;
 
		// find parentheses and +address offset surrounding the mangled name
		// its pattern is like this
		// >>>>
		//./listing1(test+0x43) [0x80487eb]
		// <<<<
		for ( char *p = symbollist[i]; *p; ++p )
		{
			if ( *p == '(' )
			{
				begin_name = p;
			}
			else if ( *p == '+' )
			{
				begin_offset = p;
			}
			else if ( *p == ')' && ( begin_offset || begin_name ))
			{
				end_offset = p;
			}
		}
 
		if ( begin_name && end_offset && ( begin_name < end_offset ))
		{
			*begin_name++   = '\0';
			*end_offset++   = '\0';
			if ( begin_offset )
			{
				*begin_offset++ = '\0';
			}

			// mangled name is now in [begin_name, begin_offset) and caller
			// offset in [begin_offset, end_offset). now apply
			// __cxa_demangle():

			int   status = 0;
			char* ret = abi::__cxa_demangle( begin_name, funcname, &funcnamesize, &status );
			char* fname = (0 == status) ? ret : begin_name;

			if ( begin_offset )
			{
				fprintf( out, "%s(%s+%s) %s\n",
					symbollist[i], fname, begin_offset, end_offset );
			}
			else
			{
				fprintf( out, "%s(%s%s) %s\n",
					symbollist[i], fname, "", end_offset );
			}
		} 
		else 
		{
			// couldn't parse the line? print the whole line.
			fprintf(out, "%s\n", symbollist[i]);
		}
	}

	free(symbollist);
}

void backtrace_for_pure_c( void ) 
{
	void *trace[16];
	char **messages = (char **)NULL;
	int i, trace_size = 0;

	trace_size = backtrace(trace, 16);
	messages = backtrace_symbols(trace, trace_size);
	printf("[bt] Execution path:\n");
	for (i=0; i<trace_size; ++i)
	{
		printf("[bt] %s\n", messages[i]);
	}
}


int func_low(int p1, int p2) 
{
	p1 = p1 - p2;
	backtrace_for_cpp();
	return 2*p1;
}

static int func_high(int p1, int p2)
{
	p1 = p1 + p2;
	backtrace_for_pure_c();
	return 2*p1;
}

static int test(int p1) 
{
	int res = 0;
	
	if ( p1 < 10 )
	{
		res = 5 + func_low(p1, 2*p1);
	}
	else
	{
		res = 5 + func_high(p1, 2*p1);
	}
	return res;
}

int main() 
{
	printf("First call: %d\n\n", test(27));
	printf("Second call: %d\n",  test(4));
}