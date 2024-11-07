function(generate_odb)
    set(options WITH_SCHEMA)
    set(oneValueArgs TARGET OUT_DIR DATABASE ENTITY_SRC)
    set(multiValueArgs IMPORTS PRAGMAS ODBC_OPTIONS)
    cmake_parse_arguments(PARSE_ARGV 0 arg "${options}" "${oneValueArgs}" "${multiValueArgs}")

    if(NOT TARGET odb::odbc)
        message(SEND_ERROR "odb::odbc target not found!")
        return()
    endif()

    if (arg_WITH_SCHEMA)
        list(PREPEND arg_ODBC_OPTIONS "--generate-schema")
    endif()

    get_filename_component(_abs_file ${arg_ENTITY_SRC} ABSOLUTE)
    get_filename_component(_abs_dir ${_abs_file} DIRECTORY)

    get_filename_component(_file_full_name ${arg_ENTITY_SRC} NAME)
    string(FIND "${_file_full_name}" "." _file_last_ext_pos REVERSE)
    string(SUBSTRING "${_file_full_name}" 0 ${_file_last_ext_pos} _basename)

    set(_generated_srcs)
    list(APPEND _generated_srcs
        "${arg_OUT_DIR}/${_basename}-odb.hxx"
        "${arg_OUT_DIR}/${_basename}-odb.cxx")
    
    list(TRANSFORM arg_IMPORTS PREPEND "-I")

    set(_epilogues)
    foreach(_pragma ${arg_PRAGMAS})
        string(CONFIGURE "#include \"${_pragma}\"" _epilogue)
        list(APPEND _epilogues "--odb-epilogue" ${_epilogue})
    endforeach()
    
    list(APPEND arg_ODBC_OPTIONS ${_epilogues})

    add_custom_command(
        OUTPUT ${_generated_srcs}
        COMMAND odb::odbc
        ARGS -d ${arg_DATABASE} ${arg_IMPORTS}
            --generate-query ${arg_ODBC_OPTIONS}
            -o ${arg_OUT_DIR}
            ${_abs_file}
        COMMENT "Compiling ${_basename} entity with ODB compiler"
        VERBATIM)
    
    set_source_files_properties(${_generated_srcs} PROPERTIES GENERATED TRUE)
    target_sources(${arg_TARGET} PRIVATE ${_generated_srcs})
endfunction(generate_odb)
