// Export decompiled functions without needing a graphical desktop.
// @category MRROBOT
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

public class ExportDecompiled extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected an output C file");
        }
        DecompInterface decompiler = new DecompInterface();
        try {
            if (!decompiler.openProgram(currentProgram)) {
                throw new IllegalStateException(decompiler.getLastMessage());
            }
            try (PrintWriter output = new PrintWriter(args[0], StandardCharsets.UTF_8)) {
                output.println("/* Ghidra decompiler output; inferred types may need correction. */");
                FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
                while (functions.hasNext() && !monitor.isCancelled()) {
                    Function function = functions.next();
                    if (function.isExternal() || function.isThunk()) continue;
                    output.println("\n/* " + function.getName() + " @ " + function.getEntryPoint() + " */");
                    DecompileResults result = decompiler.decompileFunction(function, 30, monitor);
                    if (result.decompileCompleted()) {
                        output.println(result.getDecompiledFunction().getC());
                    } else {
                        output.println("/* Decompilation unavailable for this function. */");
                    }
                }
            }
        } finally {
            decompiler.dispose();
        }
    }
}
