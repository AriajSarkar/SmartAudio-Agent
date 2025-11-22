"""
SAA CLI Application
Click-based command-line interface for audiobook generation
"""
import asyncio
import sys
import warnings
import os
from pathlib import Path
from typing import Optional
import logging

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.logging import RichHandler
from rich.panel import Panel

from saa.config import get_settings
from saa.__version__ import __version__

console = Console()


def setup_logging(verbose: bool = False):
    """Configure logging with Rich handler"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


@click.group()
@click.version_option(version=__version__, prog_name="SAA")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """
    🎙️ Smart Audio Agent (SAA) - AI-powered audiobook generator
    
    Convert PDF/TXT documents into audiobooks with character voice cloning.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='./output', help='Output directory (handles PDFs up to 100+ pages)')
@click.option('--format', '-f', type=click.Choice(['mp3', 'wav', 'ogg', 'flac']), default='mp3', help='Output format')
@click.option('--provider', '-p', type=click.Choice(['auto', 'replicate', 'local']), default='auto', help='TTS provider')
@click.option('--session-id', '-s', help='Session ID for checkpoints')
@click.pass_context
def generate(ctx, input_file, output, format, provider, session_id):
    """
    Generate audiobook from PDF or TXT file
    
    Example:
        saa generate input/mybook.pdf -o output/mybook -f mp3
    """
    verbose = ctx.obj.get('verbose', False)
    
    console.print(Panel.fit(
        f"[bold cyan]SAA Audiobook Generator v{__version__}[/bold cyan]\n"
        f"Input: {input_file}\n"
        f"Output: {output}\n"
        f"Format: {format.upper()}\n"
        f"Provider: {provider}",
        title="🎙️ Configuration",
        border_style="cyan"
    ))
    
    # Validate input file
    input_path = Path(input_file)
    if not input_path.exists():
        console.print(f"[red]❌ File not found: {input_file}[/red]")
        sys.exit(1)
    
    if input_path.suffix.lower() not in ['.pdf', '.txt']:
        console.print(f"[red]❌ Unsupported file type: {input_path.suffix}[/red]")
        console.print("[yellow]💡 Supported formats: PDF, TXT[/yellow]")
        sys.exit(1)
    
    # Run pipeline
    try:
        # Import new orchestrator
        from saa.agents.orchestrator import AudiobookOrchestrator
        
        console.print("\n[cyan]🚀 Initializing 5-stage ADK pipeline...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Generating audiobook...", total=None)
            
            # Create orchestrator
            orchestrator = AudiobookOrchestrator(
                input_file=input_path,
                output_dir=Path(output),
                job_id=session_id
            )
            
            # Run pipeline
            async def run():
                return await orchestrator.run_async()
            
            result = asyncio.run(run())
            progress.update(task, completed=True)
        
        # Check result
        if result["status"] == "success":
            console.print(f"\n✅ [bold green]Audiobook generated successfully![/bold green]")
            console.print(f"📁 Output directory: [cyan]{result['output_dir']}[/cyan]")
            console.print(f"🎵 Generated files:")
            for file in result.get("output_files", []):
                console.print(f"   • {Path(file).name}")
        else:
            console.print(f"\n[red]❌ Generation failed: {result.get('error')}[/red]")
            sys.exit(1)
        
        # Suppress aiohttp shutdown errors (professional cleanup)
        sys.stderr = open(os.devnull, 'w')
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Generation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]❌ Fatal error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--text', '-t', default='Hello, this is a test of the audiobook system.', help='Sample text')
@click.option('--output', '-o', default='./samples', help='Output directory for sample')
@click.pass_context
def sample(ctx, input_file, text, output):
    """
    Generate a short audio sample for testing
    
    Example:
        saa sample reference_audio/male.wav --text "Hello world"
    """
    console.print(Panel.fit(
        f"[bold cyan]SAA Sample Generator[/bold cyan]\n"
        f"Reference: {input_file}\n"
        f"Text: {text[:50]}...\n"
        f"Output: {output}",
        title="🎤 Sample Configuration",
        border_style="cyan"
    ))
    
    # TODO: Implement sample generation using synthesis tools
    console.print("[yellow]⚠️  Sample generation not yet implemented[/yellow]")
    console.print("[dim]Coming soon: Quick audio preview generation[/dim]")


@cli.command()
@click.argument('session_id')
@click.pass_context
def resume(ctx, session_id):
    """
    Resume audiobook generation from checkpoint
    
    Example:
        saa resume session-12345
    """
    verbose = ctx.obj.get('verbose', False)
    console.print(f"[cyan]Resuming session: {session_id}[/cyan]")
    
    # Check if session exists
    output_dir = Path("./output")
    session_dir = output_dir / session_id
    state_path = session_dir / "state.json"
    
    if not session_dir.exists() or not state_path.exists():
        console.print(f"[red]❌ Session not found: {session_id}[/red]")
        console.print(f"Expected checkpoint at: {state_path}")
        sys.exit(1)
        
    # Load state to get input file
    try:
        from saa.models import JobState
        state = JobState.load(state_path)
        input_file = state.input_file
        console.print(f"📄 Input file: {input_file}")
        console.print(f"🔄 Last stage: {state.stage.value}")
    except Exception as e:
        console.print(f"[red]❌ Failed to load checkpoint: {e}[/red]")
        sys.exit(1)

    # Run pipeline
    try:
        # Import new orchestrator
        from saa.agents.orchestrator import AudiobookOrchestrator
        
        console.print("\n[cyan]🚀 Resuming 5-stage ADK pipeline...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(f"[cyan]Resuming audiobook (Stage: {state.stage.value})...", total=None)
            
            # Create orchestrator with existing job_id
            orchestrator = AudiobookOrchestrator(
                input_file=input_file,
                output_dir=output_dir,
                job_id=session_id
            )
            
            # Run pipeline
            async def run():
                return await orchestrator.run_async()
            
            result = asyncio.run(run())
            progress.update(task, completed=True)
        
        # Check result
        if result["status"] == "success":
            console.print(f"\n✅ [bold green]Audiobook generated successfully![/bold green]")
            console.print(f"📁 Output directory: [cyan]{result['output_dir']}[/cyan]")
            console.print(f"🎵 Generated files:")
            for file in result.get("output_files", []):
                console.print(f"   • {Path(file).name}")
        else:
            console.print(f"\n[red]❌ Generation failed: {result.get('error')}[/red]")
            sys.exit(1)
        
        # Suppress aiohttp shutdown errors
        sys.stderr = open(os.devnull, 'w')
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Generation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]❌ Fatal error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.pass_context
def list_sessions(ctx):
    """
    List all saved sessions
    
    Example:
        saa list-sessions
    """
    console.print("[cyan]Listing saved sessions...[/cyan]")
    
    from rich.table import Table
    from saa.models import JobState
    
    table = Table(title="📚 Saved Sessions")
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Input File", style="magenta")
    table.add_column("Stage", style="green")
    table.add_column("Progress", justify="right")
    table.add_column("Last Updated", style="dim")
    
    output_dir = Path("./output")
    if not output_dir.exists():
        console.print("[yellow]No sessions found (output directory missing)[/yellow]")
        return

    found_sessions = False
    
    # Scan for sessions
    for session_dir in sorted(output_dir.iterdir(), key=os.path.getmtime, reverse=True):
        if not session_dir.is_dir():
            continue
            
        state_path = session_dir / "state.json"
        if state_path.exists():
            try:
                state = JobState.load(state_path)
                found_sessions = True
                
                # Format progress
                progress = f"{state.progress_percentage:.0f}%"
                if state.is_completed:
                    progress = "[bold green]DONE[/bold green]"
                elif state.is_failed:
                    progress = "[bold red]FAILED[/bold red]"
                
                table.add_row(
                    state.job_id,
                    state.input_file.name,
                    state.stage.value,
                    progress,
                    state.updated_at.strftime("%Y-%m-%d %H:%M")
                )
            except Exception:
                continue
    
    if found_sessions:
        console.print(table)
    else:
        console.print("[yellow]No saved sessions found.[/yellow]")


@cli.command()
@click.pass_context
def config(ctx):
    """
    Show current configuration
    
    Example:
        saa config
    """
    settings = get_settings()
    
    console.print(Panel.fit(
        f"[bold cyan]SAA Configuration[/bold cyan]\n\n"
        f"TTS Provider: [yellow]{settings.tts_provider}[/yellow]\n"
        f"Effective Provider: [yellow]{settings.effective_tts_provider}[/yellow]\n"
        f"Replicate Available: [yellow]{settings.has_replicate_token}[/yellow]\n"
        f"Gemini Model: [yellow]{settings.gemini_text_model}[/yellow]\n"
        f"GPU Enabled: [yellow]{settings.use_gpu}[/yellow]\n"
        f"Max Segment Length: [yellow]{settings.max_segment_length}[/yellow]\n"
        f"Output Format: [yellow]{settings.default_audio_format}[/yellow]\n"
        f"Session DB: [yellow]{settings.session_db_path}[/yellow]",
        title="⚙️ Settings",
        border_style="cyan"
    ))


if __name__ == '__main__':
    cli()
