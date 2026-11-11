const path = require('path');

// Webpack hashes ancestor directories to distinguish them from files. On macOS,
// opening Desktop can stall before Node returns EISDIR. Preserve that result
// for known directories without opening them or changing reads of real files.
class DirectoryReadGuardPlugin {
  constructor(projectDirectory) {
    this.directories = new Set();
    let directory = path.resolve(projectDirectory);
    while (!this.directories.has(directory)) {
      this.directories.add(directory);
      directory = path.dirname(directory);
    }
  }

  apply(compiler) {
    compiler.hooks.afterEnvironment.tap('DirectoryReadGuardPlugin', () => {
      const fileSystem = compiler.inputFileSystem;
      const readFile = fileSystem.readFile;
      fileSystem.readFile = (filename, ...args) => {
        const candidate = Buffer.isBuffer(filename) ? filename.toString() : filename;
        if (typeof candidate === 'string' && this.directories.has(path.resolve(candidate))) {
          const callback = args[args.length - 1];
          const error = Object.assign(new Error('EISDIR: illegal operation on a directory, read'), {
            code: 'EISDIR', errno: -21, syscall: 'read', path: candidate,
          });
          return process.nextTick(callback, error);
        }
        return readFile.call(fileSystem, filename, ...args);
      };
    });
  }
}

module.exports = DirectoryReadGuardPlugin;
