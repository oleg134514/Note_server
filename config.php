<?php
function python_exec($command) {
    $output = [];
    $return_var = 0;
    exec($command . ' 2>&1', $output, $return_var);
    $output_str = implode("\n", $output);
    error_log("Python command: $command");
    error_log("Python output: $output_str");
    error_log("Return code: $return_var");
    return [$output, $return_var];
}
?>