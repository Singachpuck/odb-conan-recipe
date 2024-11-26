if(NOT TARGET odb::odbc)
    if(CMAKE_CROSSCOMPILING)
        find_program(ODBC_PROGRAM NAMES odb PATHS ENV PATH NO_DEFAULT_PATH)
    endif()

    if(NOT ODBC_PROGRAM)
        find_program(ODBC_PROGRAM NAMES odb PATHS "${odb_compiler_PACKAGE_FOLDER_RELEASE}/bin")
    endif()

    if(NOT ODBC_PROGRAM)
        message(WARNING "ODB compiler is not found! Consider setting Odb_ODBC_EXECUTABLE.")
    endif()

    get_filename_component(ODBC_PROGRAM "${ODBC_PROGRAM}" ABSOLUTE)

    set(Odb_ODBC_EXECUTABLE ${ODBC_PROGRAM} CACHE FILEPATH "The odb compiler")

    add_executable(odb::odbc IMPORTED)
    set_property(TARGET odb::odbc PROPERTY IMPORTED_LOCATION ${Odb_ODBC_EXECUTABLE})
endif()